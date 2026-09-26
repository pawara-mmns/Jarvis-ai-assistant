import { describe, expect, it } from "vitest";
import { resolveAudioDrivenState } from "./state-integration";

describe("audio-driven assistant state", () => {
  it("moves idle to listening when speech is detected", () => {
    expect(resolveAudioDrivenState("idle", true, true)).toBe("listening");
  });

  it("moves listening to idle after speech ends", () => {
    expect(resolveAudioDrivenState("listening", true, false)).toBe("idle");
  });

  it.each(["thinking", "executing", "speaking", "confirmation", "error"] as const)(
    "does not overwrite the %s state",
    (state) => {
      expect(resolveAudioDrivenState(state, true, true)).toBe(state);
      expect(resolveAudioDrivenState(state, true, false)).toBe(state);
    },
  );
});
