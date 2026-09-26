import { describe, expect, it } from "vitest";
import { EnergyVad, type VadConfig } from "./vad";

const testConfig: VadConfig = {
  speechStartThreshold: 0.2,
  speechEndThreshold: 0.1,
  minimumSpeechMs: 100,
  speechEndDelayMs: 400,
};

describe("EnergyVad", () => {
  it("keeps silence classified as silence", () => {
    const vad = new EnergyVad(testConfig);

    expect(vad.update(0.02, 0)).toBe(false);
    expect(vad.update(0.08, 500)).toBe(false);
  });

  it("requires sustained energy before speech starts", () => {
    const vad = new EnergyVad(testConfig);

    expect(vad.update(0.3, 0)).toBe(false);
    expect(vad.update(0.3, 80)).toBe(false);
    expect(vad.update(0.3, 110)).toBe(true);
  });

  it("does not end speech during a brief energy dip", () => {
    const vad = new EnergyVad(testConfig);
    vad.update(0.3, 0);
    vad.update(0.3, 120);

    expect(vad.update(0.02, 200)).toBe(true);
    expect(vad.update(0.02, 500)).toBe(true);
    expect(vad.update(0.25, 520)).toBe(true);
  });

  it("ends speech after sustained silence", () => {
    const vad = new EnergyVad(testConfig);
    vad.update(0.3, 0);
    vad.update(0.3, 120);

    expect(vad.update(0.02, 200)).toBe(true);
    expect(vad.update(0.02, 610)).toBe(false);
  });
});
