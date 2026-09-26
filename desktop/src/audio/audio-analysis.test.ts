import { describe, expect, it } from "vitest";
import {
  calculateRms,
  normalizeAudioLevel,
  smoothAudioLevel,
  summarizeWaveform,
} from "./audio-analysis";

describe("audio analysis", () => {
  it("calculates RMS energy instead of a raw peak", () => {
    expect(calculateRms([1, -1, 1, -1])).toBe(1);
    expect(calculateRms([0.5, -0.5, 0.5, -0.5])).toBe(0.5);
    expect(calculateRms([])).toBe(0);
  });

  it("normalizes silence and voice energy into 0..1", () => {
    const options = { noiseFloor: 0.01, referenceLevel: 0.11, responseCurve: 1 };

    expect(normalizeAudioLevel(0.005, options)).toBe(0);
    expect(normalizeAudioLevel(0.06, options)).toBeCloseTo(0.5);
    expect(normalizeAudioLevel(0.3, options)).toBe(1);
  });

  it("uses a faster attack and slower release", () => {
    const options = { attack: 0.5, release: 0.1 };

    expect(smoothAudioLevel(0, 1, options)).toBe(0.5);
    expect(smoothAudioLevel(1, 0, options)).toBe(0.9);
  });

  it("downsamples samples to compact normalized waveform levels", () => {
    const levels = summarizeWaveform(
      [0, 0, 0.05, -0.05, 0.1, -0.1, 0.2, -0.2],
      4,
      { noiseFloor: 0, referenceLevel: 0.2, responseCurve: 1 },
    );

    expect(levels).toHaveLength(4);
    expect(levels[0]).toBe(0);
    expect(levels[1]).toBeCloseTo(0.25);
    expect(levels[2]).toBeCloseTo(0.5);
    expect(levels[3]).toBe(1);
  });
});
