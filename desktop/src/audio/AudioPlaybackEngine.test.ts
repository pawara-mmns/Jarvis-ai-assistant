import { describe, expect, it } from "vitest";
import { summarizePcm16 } from "./AudioPlaybackEngine";

describe("output audio analysis", () => {
  it("derives real normalized playback levels for the UI", () => {
    const quiet = summarizePcm16(new Int16Array(240), 24);
    const loud = summarizePcm16(new Int16Array(240).fill(20_000), 24);
    expect(quiet).toHaveLength(24);
    expect(Math.max(...quiet)).toBe(0);
    expect(Math.min(...loud)).toBeGreaterThan(0.9);
  });
});

