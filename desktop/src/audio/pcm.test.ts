import { describe, expect, it } from "vitest";
import {
  Pcm16Chunker,
  StreamingPcm16Resampler,
  bytesToPcm16,
  floatToPcm16,
  pcm16ToBytes,
  sampleRateFromMimeType,
} from "./pcm";

describe("PCM conversion", () => {
  it("clamps Float32 samples into signed little-endian PCM16", () => {
    const pcm = Int16Array.from([-32_768, 0, 32_767]);
    expect(floatToPcm16(-2)).toBe(-32_768);
    expect(floatToPcm16(2)).toBe(32_767);
    expect(Array.from(bytesToPcm16(pcm16ToBytes(pcm)))).toEqual(Array.from(pcm));
  });

  it("resamples a continuous 48 kHz stream to 16 kHz", () => {
    const resampler = new StreamingPcm16Resampler(16_000);
    const first = resampler.push(new Float32Array(2_400).fill(0.5), 48_000);
    const second = resampler.push(new Float32Array(2_400).fill(0.5), 48_000);
    expect(first.length + second.length).toBeCloseTo(1_600, -1);
    expect(first[20]).toBeGreaterThan(16_000);
  });

  it("emits low-latency fixed chunks and retains a final partial chunk", () => {
    const chunker = new Pcm16Chunker(640);
    const chunks = chunker.push(new Int16Array(1_500));
    expect(chunks.map((chunk) => chunk.length)).toEqual([640, 640]);
    expect(chunker.flush()?.length).toBe(220);
    expect(sampleRateFromMimeType("audio/pcm;rate=24000")).toBe(24_000);
  });
});

