import { base64ToBytes, bytesToPcm16, sampleRateFromMimeType } from "./pcm";

export interface PlaybackSnapshot {
  state: "idle" | "playing" | "error";
  level: number;
  waveformLevels: readonly number[];
  queuedChunks: number;
  error?: string;
}

type PlaybackListener = (snapshot: PlaybackSnapshot) => void;

const emptyWaveform = (): number[] => new Array<number>(24).fill(0);

export function summarizePcm16(samples: Int16Array, bucketCount = 24): number[] {
  if (!samples.length) return new Array<number>(bucketCount).fill(0);
  const bucketSize = Math.max(1, Math.floor(samples.length / bucketCount));
  return Array.from({ length: bucketCount }, (_, bucket) => {
    const start = bucket * bucketSize;
    const end = bucket === bucketCount - 1 ? samples.length : Math.min(samples.length, start + bucketSize);
    let sumSquares = 0;
    for (let index = start; index < end; index += 1) {
      const sample = samples[index] / 32_768;
      sumSquares += sample * sample;
    }
    return Math.min(1, Math.sqrt(sumSquares / Math.max(1, end - start)) * 2.5);
  });
}

export class AudioPlaybackEngine {
  private context: AudioContext | null = null;
  private nextStartTime = 0;
  private generation = 0;
  private readonly sources = new Set<AudioBufferSourceNode>();
  private readonly listeners = new Set<PlaybackListener>();
  private snapshot: PlaybackSnapshot = {
    state: "idle",
    level: 0,
    waveformLevels: emptyWaveform(),
    queuedChunks: 0,
  };

  async prepare(): Promise<void> {
    if (!this.context || this.context.state === "closed") {
      this.context = new AudioContext({ latencyHint: "interactive" });
      this.nextStartTime = this.context.currentTime;
    }
    if (this.context.state === "suspended") await this.context.resume();
  }

  subscribe(listener: PlaybackListener): () => void {
    this.listeners.add(listener);
    listener(this.snapshot);
    return () => this.listeners.delete(listener);
  }

  async enqueue(base64Audio: string, mimeType: string): Promise<void> {
    try {
      const generation = this.generation;
      await this.prepare();
      if (generation !== this.generation) return;
      const context = this.context;
      if (!context) return;
      const pcm = bytesToPcm16(base64ToBytes(base64Audio));
      if (!pcm.length) return;
      const sampleRate = sampleRateFromMimeType(mimeType);
      const buffer = context.createBuffer(1, pcm.length, sampleRate);
      const channel = buffer.getChannelData(0);
      let sumSquares = 0;
      for (let index = 0; index < pcm.length; index += 1) {
        const sample = pcm[index] / 32_768;
        channel[index] = sample;
        sumSquares += sample * sample;
      }

      const source = context.createBufferSource();
      source.buffer = buffer;
      source.connect(context.destination);
      const startAt = Math.max(context.currentTime + 0.015, this.nextStartTime);
      this.nextStartTime = startAt + buffer.duration;
      this.sources.add(source);
      source.onended = () => {
        source.disconnect();
        this.sources.delete(source);
        if (!this.sources.size) {
          this.nextStartTime = context.currentTime;
          this.update({ state: "idle", level: 0, waveformLevels: emptyWaveform(), queuedChunks: 0 });
        } else {
          this.update({ queuedChunks: this.sources.size });
        }
      };
      this.update({
        state: "playing",
        level: Math.min(1, Math.sqrt(sumSquares / pcm.length) * 2.5),
        waveformLevels: summarizePcm16(pcm),
        queuedChunks: this.sources.size,
        error: undefined,
      });
      source.start(startAt);
    } catch (error) {
      console.warn("[audio] output playback failed", error);
      this.update({ state: "error", error: "Gemini audio playback failed." });
    }
  }

  stop(): void {
    this.generation += 1;
    for (const source of this.sources) {
      source.onended = null;
      try {
        source.stop();
      } catch {
        // Source may already have ended.
      }
      source.disconnect();
    }
    this.sources.clear();
    if (this.context) this.nextStartTime = this.context.currentTime;
    this.update({ state: "idle", level: 0, waveformLevels: emptyWaveform(), queuedChunks: 0 });
  }

  async dispose(): Promise<void> {
    this.stop();
    const context = this.context;
    this.context = null;
    if (context && context.state !== "closed") await context.close().catch(() => undefined);
    this.listeners.clear();
  }

  private update(update: Partial<PlaybackSnapshot>): void {
    this.snapshot = { ...this.snapshot, ...update };
    for (const listener of this.listeners) listener(this.snapshot);
  }
}

export const audioPlaybackEngine = new AudioPlaybackEngine();
