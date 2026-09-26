import {
  calculateRms,
  normalizeAudioLevel,
  smoothAudioLevel,
  smoothWaveform,
  summarizeWaveform,
} from "./audio-analysis";
import { getMicrophoneErrorMessage } from "./audio-errors";
import type {
  AudioEngineSnapshot,
  AudioFrameListener,
  AudioInputDevice,
  AudioSnapshotListener,
  MicrophonePermissionState,
} from "./audio.types";
import { EnergyVad } from "./vad";

const WAVEFORM_BAR_COUNT = 24;
const UI_UPDATE_INTERVAL_MS = 1000 / 30;
const emptyWaveform = (): number[] => new Array<number>(WAVEFORM_BAR_COUNT).fill(0);

export class AudioEngine {
  private stream: MediaStream | null = null;
  private context: AudioContext | null = null;
  private source: MediaStreamAudioSourceNode | null = null;
  private analyser: AnalyserNode | null = null;
  private captureNode: AudioWorkletNode | null = null;
  private silentOutput: GainNode | null = null;
  private samples: Float32Array<ArrayBuffer> | null = null;
  private animationFrameId: number | null = null;
  private startPromise: Promise<void> | null = null;
  private operationId = 0;
  private monitoringDevices = false;
  private lastUiUpdateAt = 0;
  private smoothedLevel = 0;
  private waveformLevels = emptyWaveform();
  private readonly vad = new EnergyVad();
  private readonly snapshotListeners = new Set<AudioSnapshotListener>();
  private readonly frameListeners = new Set<AudioFrameListener>();

  private snapshot: AudioEngineSnapshot = {
    status: "idle",
    permissionState: "unknown",
    devices: [],
    selectedDeviceId: undefined,
    audioLevel: 0,
    waveformLevels: emptyWaveform(),
    speechDetected: false,
    error: undefined,
  };

  async initialize(): Promise<void> {
    if (!navigator.mediaDevices?.getUserMedia) {
      this.updateSnapshot({
        permissionState: "unavailable",
        status: "error",
        error: "Microphone capture is unavailable in this environment.",
      });
      return;
    }

    if (!this.monitoringDevices) {
      navigator.mediaDevices.addEventListener("devicechange", this.handleDeviceChange);
      this.monitoringDevices = true;
    }

    await Promise.all([this.refreshPermissionState(), this.refreshDevices()]);
  }

  subscribe(listener: AudioSnapshotListener): () => void {
    this.snapshotListeners.add(listener);
    listener(this.snapshot);
    return () => this.snapshotListeners.delete(listener);
  }

  subscribeToAudioFrames(listener: AudioFrameListener): () => void {
    this.frameListeners.add(listener);
    return () => this.frameListeners.delete(listener);
  }

  async start(deviceId?: string): Promise<void> {
    if (this.startPromise) return this.startPromise;
    if (this.stream && (!deviceId || this.snapshot.selectedDeviceId === deviceId)) return;
    if (this.stream) await this.stop();

    const operationId = ++this.operationId;
    this.startPromise = this.startInternal(operationId, deviceId);
    try {
      await this.startPromise;
    } finally {
      this.startPromise = null;
    }
  }

  async stop(): Promise<void> {
    this.operationId += 1;
    this.stopAnalysisLoop();
    this.source?.disconnect();
    this.source = null;
    this.analyser?.disconnect();
    this.analyser = null;
    if (this.captureNode) {
      this.captureNode.port.onmessage = null;
      this.captureNode.disconnect();
      this.captureNode = null;
    }
    this.silentOutput?.disconnect();
    this.silentOutput = null;

    for (const track of this.stream?.getTracks() ?? []) track.stop();
    this.stream = null;

    const context = this.context;
    this.context = null;
    if (context && context.state !== "closed") {
      await context.close().catch(() => undefined);
    }

    this.samples = null;
    this.smoothedLevel = 0;
    this.waveformLevels = emptyWaveform();
    this.vad.reset();
    this.updateSnapshot({
      status: "idle",
      audioLevel: 0,
      waveformLevels: this.waveformLevels,
      speechDetected: false,
      error: undefined,
    });
  }

  async switchDevice(deviceId: string): Promise<void> {
    const wasActive = this.snapshot.status === "active" || this.snapshot.status === "starting";
    await this.stop();
    this.updateSnapshot({ selectedDeviceId: deviceId });
    if (wasActive) await this.start(deviceId);
  }

  async getDevices(): Promise<readonly AudioInputDevice[]> {
    await this.refreshDevices();
    return this.snapshot.devices;
  }

  async dispose(): Promise<void> {
    if (this.monitoringDevices && navigator.mediaDevices) {
      navigator.mediaDevices.removeEventListener("devicechange", this.handleDeviceChange);
      this.monitoringDevices = false;
    }
    await this.stop();
    this.frameListeners.clear();
  }

  private async startInternal(operationId: number, deviceId?: string): Promise<void> {
    if (!navigator.mediaDevices?.getUserMedia) {
      this.updateSnapshot({
        status: "error",
        permissionState: "unavailable",
        error: "Microphone capture is unavailable in this environment.",
      });
      return;
    }

    this.updateSnapshot({ status: "starting", error: undefined });

    let stream: MediaStream | null = null;
    let context: AudioContext | null = null;
    try {
      stream = await navigator.mediaDevices.getUserMedia({
        video: false,
        audio: {
          ...(deviceId ? { deviceId: { exact: deviceId } } : {}),
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          channelCount: 1,
        },
      });

      if (operationId !== this.operationId) {
        for (const track of stream.getTracks()) track.stop();
        return;
      }

      context = new AudioContext({ latencyHint: "interactive" });
      const source = context.createMediaStreamSource(stream);
      const analyser = context.createAnalyser();
      analyser.fftSize = 1024;
      analyser.smoothingTimeConstant = 0.58;
      source.connect(analyser);
      if (context.state === "suspended") await context.resume();

      let captureNode: AudioWorkletNode | null = null;
      let silentOutput: GainNode | null = null;
      try {
        const workletUrl = new URL("./pcm-capture.worklet.js", import.meta.url);
        await context.audioWorklet.addModule(workletUrl);
        captureNode = new AudioWorkletNode(context, "jarvis-pcm-capture", {
          numberOfInputs: 1,
          numberOfOutputs: 1,
          outputChannelCount: [1],
        });
        silentOutput = context.createGain();
        silentOutput.gain.value = 0;
        const captureSampleRate = context.sampleRate;
        captureNode.port.onmessage = (event: MessageEvent<unknown>) => {
          if (!(event.data instanceof Float32Array)) return;
          const frame = {
            samples: event.data,
            sampleRate: captureSampleRate,
            timestamp: performance.now(),
          };
          for (const listener of this.frameListeners) listener(frame);
        };
        source.connect(captureNode);
        captureNode.connect(silentOutput);
        silentOutput.connect(context.destination);
      } catch (error) {
        console.warn("[audio] continuous PCM capture unavailable; using analysis fallback", error);
      }

      this.stream = stream;
      this.context = context;
      this.source = source;
      this.analyser = analyser;
      this.captureNode = captureNode;
      this.silentOutput = silentOutput;
      this.samples = new Float32Array(analyser.fftSize);
      this.smoothedLevel = 0;
      this.waveformLevels = emptyWaveform();
      this.vad.reset();

      const track = stream.getAudioTracks()[0];
      const activeDeviceId = track?.getSettings().deviceId ?? deviceId;
      track?.addEventListener("ended", this.handleTrackEnded, { once: true });

      this.updateSnapshot({
        status: "active",
        permissionState: "granted",
        selectedDeviceId: activeDeviceId,
        audioLevel: 0,
        waveformLevels: this.waveformLevels,
        speechDetected: false,
        error: undefined,
      });
      await this.refreshDevices();
      this.startAnalysisLoop();
    } catch (error) {
      for (const track of stream?.getTracks() ?? []) track.stop();
      if (context && context.state !== "closed") await context.close().catch(() => undefined);
      const message = getMicrophoneErrorMessage(error);
      const permissionState = this.getPermissionStateFromError(error);
      console.warn("[audio] microphone startup failed", error);
      this.updateSnapshot({ status: "error", permissionState, error: message });
    }
  }

  private startAnalysisLoop(): void {
    this.stopAnalysisLoop();
    this.lastUiUpdateAt = 0;

    const analyze = (timestamp: number) => {
      const analyser = this.analyser;
      const samples = this.samples;
      const context = this.context;
      if (!analyser || !samples || !context) return;

      analyser.getFloatTimeDomainData(samples);
      const normalizedLevel = normalizeAudioLevel(calculateRms(samples));
      this.smoothedLevel = smoothAudioLevel(this.smoothedLevel, normalizedLevel);

      if (!this.captureNode && this.frameListeners.size) {
        const frame = { samples, sampleRate: context.sampleRate, timestamp };
        for (const listener of this.frameListeners) listener(frame);
      }

      if (timestamp - this.lastUiUpdateAt >= UI_UPDATE_INTERVAL_MS) {
        this.lastUiUpdateAt = timestamp;
        const summarized = summarizeWaveform(samples, WAVEFORM_BAR_COUNT);
        this.waveformLevels = smoothWaveform(this.waveformLevels, summarized);
        const speechDetected = this.vad.update(this.smoothedLevel, timestamp);
        this.updateSnapshot({
          audioLevel: this.smoothedLevel,
          waveformLevels: this.waveformLevels,
          speechDetected,
        });
      }

      this.animationFrameId = requestAnimationFrame(analyze);
    };

    this.animationFrameId = requestAnimationFrame(analyze);
  }

  private stopAnalysisLoop(): void {
    if (this.animationFrameId !== null) cancelAnimationFrame(this.animationFrameId);
    this.animationFrameId = null;
  }

  private async refreshPermissionState(): Promise<void> {
    if (!navigator.permissions?.query) return;
    try {
      const permission = await navigator.permissions.query({ name: "microphone" as PermissionName });
      this.updateSnapshot({ permissionState: permission.state as MicrophonePermissionState });
    } catch {
      // Chromium may not expose microphone permission state before the first request.
    }
  }

  private async refreshDevices(): Promise<void> {
    if (!navigator.mediaDevices?.enumerateDevices) return;
    try {
      const devices = (await navigator.mediaDevices.enumerateDevices())
        .filter((device) => device.kind === "audioinput")
        .map((device) => ({ deviceId: device.deviceId, label: device.label }));
      this.updateSnapshot({ devices });
    } catch (error) {
      console.warn("[audio] unable to enumerate microphones", error);
    }
  }

  private readonly handleDeviceChange = async (): Promise<void> => {
    await this.refreshDevices();
    const selectedDeviceId = this.snapshot.selectedDeviceId;
    if (
      this.snapshot.status === "active" &&
      selectedDeviceId &&
      !this.snapshot.devices.some((device) => device.deviceId === selectedDeviceId)
    ) {
      await this.stop();
      this.updateSnapshot({
        status: "error",
        selectedDeviceId: undefined,
        error: "The selected microphone is no longer available.",
      });
    }
  };

  private readonly handleTrackEnded = (): void => {
    if (this.snapshot.status !== "active") return;
    void this.stop().then(() => {
      this.updateSnapshot({ status: "error", error: "The microphone stopped unexpectedly." });
    });
  };

  private getPermissionStateFromError(error: unknown): MicrophonePermissionState {
    if (error instanceof DOMException && ["NotAllowedError", "SecurityError"].includes(error.name)) {
      return "denied";
    }
    return this.snapshot.permissionState;
  }

  private updateSnapshot(update: Partial<AudioEngineSnapshot>): void {
    this.snapshot = { ...this.snapshot, ...update };
    for (const listener of this.snapshotListeners) listener(this.snapshot);
  }
}

export const audioEngine = new AudioEngine();
