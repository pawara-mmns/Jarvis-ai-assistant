const PCM16_MIN = -32_768;
const PCM16_MAX = 32_767;

export function floatToPcm16(sample: number): number {
  const clamped = Math.max(-1, Math.min(1, sample));
  return Math.round(clamped < 0 ? clamped * -PCM16_MIN : clamped * PCM16_MAX);
}

export class StreamingPcm16Resampler {
  private sourceRate = 0;
  private position = 0;
  private lastSample: number | undefined;

  constructor(private readonly targetRate = 16_000) {}

  push(input: Float32Array, sourceRate: number): Int16Array {
    if (!Number.isFinite(sourceRate) || sourceRate <= 0 || input.length === 0) {
      return new Int16Array(0);
    }
    if (sourceRate !== this.sourceRate) {
      this.reset();
      this.sourceRate = sourceRate;
    }

    const source = new Float32Array(input.length + (this.lastSample === undefined ? 0 : 1));
    let offset = 0;
    if (this.lastSample !== undefined) {
      source[0] = this.lastSample;
      offset = 1;
    }
    source.set(input, offset);
    if (source.length < 2) {
      this.lastSample = source[0];
      return new Int16Array(0);
    }

    const ratio = sourceRate / this.targetRate;
    const output: number[] = [];
    while (this.position < source.length - 1) {
      const leftIndex = Math.floor(this.position);
      const fraction = this.position - leftIndex;
      const sample = source[leftIndex] + (source[leftIndex + 1] - source[leftIndex]) * fraction;
      output.push(floatToPcm16(sample));
      this.position += ratio;
    }

    this.position -= source.length - 1;
    this.lastSample = source[source.length - 1];
    return Int16Array.from(output);
  }

  reset(): void {
    this.sourceRate = 0;
    this.position = 0;
    this.lastSample = undefined;
  }
}

export class Pcm16Chunker {
  private pending: number[] = [];

  constructor(private readonly samplesPerChunk = 640) {}

  push(samples: Int16Array): Int16Array[] {
    for (const sample of samples) this.pending.push(sample);
    const chunks: Int16Array[] = [];
    while (this.pending.length >= this.samplesPerChunk) {
      chunks.push(Int16Array.from(this.pending.splice(0, this.samplesPerChunk)));
    }
    return chunks;
  }

  flush(): Int16Array | undefined {
    if (!this.pending.length) return undefined;
    const finalChunk = Int16Array.from(this.pending);
    this.pending = [];
    return finalChunk;
  }

  reset(): void {
    this.pending = [];
  }
}

export function pcm16ToBytes(samples: Int16Array): Uint8Array {
  const bytes = new Uint8Array(samples.length * 2);
  const view = new DataView(bytes.buffer);
  samples.forEach((sample, index) => view.setInt16(index * 2, sample, true));
  return bytes;
}

export function bytesToPcm16(bytes: Uint8Array): Int16Array {
  const sampleCount = Math.floor(bytes.byteLength / 2);
  const samples = new Int16Array(sampleCount);
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  for (let index = 0; index < sampleCount; index += 1) {
    samples[index] = view.getInt16(index * 2, true);
  }
  return samples;
}

export function bytesToBase64(bytes: Uint8Array): string {
  let binary = "";
  for (let index = 0; index < bytes.length; index += 1) {
    binary += String.fromCharCode(bytes[index]);
  }
  return btoa(binary);
}

export function base64ToBytes(value: string): Uint8Array {
  const binary = atob(value);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) bytes[index] = binary.charCodeAt(index);
  return bytes;
}

export function sampleRateFromMimeType(mimeType: string, fallback = 24_000): number {
  const match = /(?:^|;)rate=(\d+)(?:;|$)/.exec(mimeType);
  const parsed = Number(match?.[1]);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

