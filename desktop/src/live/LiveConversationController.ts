import { LIVE_MESSAGE_TYPES, type LiveServerMessage } from "@shared/schemas/live";
import { audioEngine } from "../audio/AudioEngine";
import { audioPlaybackEngine, type PlaybackSnapshot } from "../audio/AudioPlaybackEngine";
import { Pcm16Chunker, StreamingPcm16Resampler, pcm16ToBytes } from "../audio/pcm";
import type { AudioFrame } from "../audio/audio.types";
import { useAssistantUiStore } from "../stores/assistant-ui.store";
import { useAudioStore } from "../stores/audio.store";
import { useLiveStore } from "../stores/live.store";
import { liveBackendClient } from "./live-client";
import { mergeTranscript } from "./transcript";
import { resolveLiveAssistantState } from "./live-state";

const PRE_ROLL_CHUNKS = 6;

export class LiveConversationController {
  private initialized = false;
  private previousSpeech = false;
  private turnComplete = false;
  private pendingAudioEnqueues = 0;
  private readonly resampler = new StreamingPcm16Resampler(16_000);
  private readonly chunker = new Pcm16Chunker(640);
  private preRoll: Uint8Array[] = [];
  private unsubscribers: Array<() => void> = [];

  initialize(): void {
    if (this.initialized) return;
    this.initialized = true;
    this.unsubscribers = [
      liveBackendClient.subscribe((message) => this.handleMessage(message)),
      audioEngine.subscribeToAudioFrames((frame) => this.handleAudioFrame(frame)),
      useAudioStore.subscribe((state) => this.handleSpeechState(state.speechDetected)),
      audioPlaybackEngine.subscribe((snapshot) => this.handlePlayback(snapshot)),
    ];
  }

  async connect(): Promise<void> {
    this.initialize();
    const live = useLiveStore.getState();
    if (["connecting", "ready", "active"].includes(live.connectionState)) return;
    if (useAudioStore.getState().status !== "active") {
      live.setError("Enable the microphone before connecting AI.");
      return;
    }

    live.setError(undefined);
    live.setConnectionState("connecting");
    useAssistantUiStore.setState({
      state: "idle",
      inputSource: "microphone",
      transcript: "",
      responseText: "",
      executionLabel: undefined,
      errorMessage: undefined,
    });
    try {
      await audioPlaybackEngine.prepare();
      await liveBackendClient.connect();
    } catch (error) {
      console.warn("[live] local connection failed", error);
      live.setConnectionState("error");
      live.setError("Could not connect to the local AI service.");
      useAssistantUiStore.setState({
        state: "error",
        errorMessage: "Could not connect to the local AI service.",
      });
    }
  }

  disconnect(): void {
    const live = useLiveStore.getState();
    if (live.connectionState === "disconnected") return;
    live.setConnectionState("closing");
    live.setStreaming(false);
    liveBackendClient.disconnect();
    audioPlaybackEngine.stop();
    this.resetAudioPipeline();
    useAssistantUiStore.setState({
      state: "idle",
      executionLabel: undefined,
      errorMessage: undefined,
    });
  }

  dispose(): void {
    this.disconnect();
    for (const unsubscribe of this.unsubscribers) unsubscribe();
    this.unsubscribers = [];
    this.initialized = false;
    void audioPlaybackEngine.dispose();
  }

  private handleAudioFrame(frame: AudioFrame): void {
    const live = useLiveStore.getState();
    if (!['ready', 'active'].includes(live.connectionState)) return;
    live.setInputSampleRate(frame.sampleRate);
    const resampled = this.resampler.push(frame.samples, frame.sampleRate);
    const chunks = this.chunker.push(resampled);
    for (const chunk of chunks) this.routeAudioChunk(pcm16ToBytes(chunk));
  }

  private routeAudioChunk(bytes: Uint8Array): void {
    const live = useLiveStore.getState();
    if (!this.previousSpeech) {
      this.preRoll.push(bytes);
      if (this.preRoll.length > PRE_ROLL_CHUNKS) this.preRoll.shift();
      return;
    }
    if (!live.streaming) {
      for (const preRollChunk of this.preRoll) liveBackendClient.sendAudio(preRollChunk);
      this.preRoll = [];
      live.setStreaming(true);
      live.setConnectionState("active");
    }
    liveBackendClient.sendAudio(bytes);
  }

  private handleSpeechState(speechDetected: boolean): void {
    if (speechDetected === this.previousSpeech) return;
    this.previousSpeech = speechDetected;
    const live = useLiveStore.getState();
    if (!['ready', 'active'].includes(live.connectionState)) return;

    if (speechDetected) {
      this.turnComplete = false;
      audioPlaybackEngine.stop();
      useAssistantUiStore.setState({
        state: resolveLiveAssistantState("speech.started"),
        transcript: "",
        responseText: "",
        executionLabel: undefined,
        errorMessage: undefined,
      });
      return;
    }

    if (live.streaming) {
      const finalChunk = this.chunker.flush();
      if (finalChunk?.length) liveBackendClient.sendAudio(pcm16ToBytes(finalChunk));
      liveBackendClient.endAudio();
      live.setStreaming(false);
      useAssistantUiStore.setState({ state: resolveLiveAssistantState("speech.ended") });
    }
  }

  private handleMessage(message: LiveServerMessage): void {
    const live = useLiveStore.getState();
    const assistant = useAssistantUiStore.getState();
    switch (message.type) {
      case LIVE_MESSAGE_TYPES.sessionReady:
        live.setConnectionState("ready");
        live.setInputSampleRate(message.inputSampleRate);
        live.setError(undefined);
        break;
      case LIVE_MESSAGE_TYPES.sessionState:
        live.setConnectionState(message.state === "ready" ? "ready" : "connecting");
        break;
      case LIVE_MESSAGE_TYPES.transcriptInput:
        assistant.setTranscript(mergeTranscript(assistant.transcript, message.text));
        break;
      case LIVE_MESSAGE_TYPES.transcriptOutput:
        assistant.setResponseText(mergeTranscript(assistant.responseText, message.text));
        break;
      case LIVE_MESSAGE_TYPES.audioOutput:
        this.turnComplete = false;
        assistant.setState(resolveLiveAssistantState("output.started"));
        this.pendingAudioEnqueues += 1;
        void audioPlaybackEngine.enqueue(message.data, message.mimeType).finally(() => {
          this.pendingAudioEnqueues = Math.max(0, this.pendingAudioEnqueues - 1);
          if (
            this.turnComplete &&
            this.pendingAudioEnqueues === 0 &&
            useLiveStore.getState().outputPlaybackState === "idle"
          ) {
            this.finishTurn();
          }
        });
        break;
      case LIVE_MESSAGE_TYPES.toolStarted:
        this.turnComplete = false;
        assistant.setExecutionLabel(message.label);
        assistant.setState(resolveLiveAssistantState("tool.started"));
        break;
      case LIVE_MESSAGE_TYPES.toolCompleted:
        assistant.setExecutionLabel(message.message);
        assistant.setState(resolveLiveAssistantState("tool.completed"));
        break;
      case LIVE_MESSAGE_TYPES.toolFailed:
        assistant.setExecutionLabel(message.message);
        assistant.setState(resolveLiveAssistantState("tool.failed"));
        break;
      case LIVE_MESSAGE_TYPES.turnComplete:
        this.turnComplete = true;
        if (
          this.pendingAudioEnqueues === 0 &&
          useLiveStore.getState().outputPlaybackState === "idle"
        ) {
          this.finishTurn();
        }
        break;
      case LIVE_MESSAGE_TYPES.sessionInterrupted:
        this.turnComplete = false;
        audioPlaybackEngine.stop();
        assistant.setState(this.previousSpeech ? "listening" : "idle");
        break;
      case LIVE_MESSAGE_TYPES.sessionError: {
        const notConfigured = message.code === "not_configured";
        live.setConnectionState(notConfigured ? "not_configured" : "error");
        live.setError(message.message);
        assistant.setState(resolveLiveAssistantState("failed"));
        assistant.setErrorMessage(message.message);
        break;
      }
      case LIVE_MESSAGE_TYPES.sessionClosed:
        if (live.connectionState !== "not_configured" && live.connectionState !== "error") {
          live.reset();
          assistant.setState("idle");
        }
        this.resetAudioPipeline();
        break;
      default:
        break;
    }
  }

  private handlePlayback(snapshot: PlaybackSnapshot): void {
    const live = useLiveStore.getState();
    live.setPlayback(snapshot.state, snapshot.level, snapshot.waveformLevels);
    if (snapshot.state === "playing") {
      useAssistantUiStore.getState().setState(resolveLiveAssistantState("output.started"));
    }
    if (snapshot.state === "error") {
      live.setError(snapshot.error);
      useAssistantUiStore.setState({ state: "error", errorMessage: snapshot.error });
    }
    if (snapshot.state === "idle" && this.turnComplete && this.pendingAudioEnqueues === 0) {
      this.finishTurn();
    }
  }

  private finishTurn(): void {
    this.turnComplete = false;
    this.pendingAudioEnqueues = 0;
    const live = useLiveStore.getState();
    if (live.connectionState === "active") live.setConnectionState("ready");
    useAssistantUiStore.getState().setState(resolveLiveAssistantState("output.completed"));
  }

  private resetAudioPipeline(): void {
    this.resampler.reset();
    this.chunker.reset();
    this.preRoll = [];
    this.previousSpeech = false;
    this.turnComplete = false;
  }
}

export const liveConversationController = new LiveConversationController();
