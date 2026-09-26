import { describe, expect, it } from "vitest";
import { getMicrophoneErrorMessage } from "./audio-errors";

describe("microphone error messages", () => {
  it("maps common media errors to concise messages", () => {
    expect(getMicrophoneErrorMessage(new DOMException("blocked", "NotAllowedError"))).toBe(
      "Microphone permission was denied.",
    );
    expect(getMicrophoneErrorMessage(new DOMException("missing", "NotFoundError"))).toBe(
      "No compatible microphone was detected.",
    );
    expect(getMicrophoneErrorMessage(new Error("unknown"))).toBe(
      "Unable to access the microphone.",
    );
  });
});
