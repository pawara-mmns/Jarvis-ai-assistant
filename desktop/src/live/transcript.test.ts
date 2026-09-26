import { describe, expect, it } from "vitest";
import { mergeTranscript } from "./transcript";

describe("live transcript accumulation", () => {
  it("handles cumulative and delta updates without repeated text", () => {
    expect(mergeTranscript("Hello", "Hello Jarvis")).toBe("Hello Jarvis");
    expect(mergeTranscript("Hello Jarvis", " Jarvis, can you hear me?")).toBe(
      "Hello Jarvis, can you hear me?",
    );
    expect(mergeTranscript("හෙලෝ", "JARVIS")).toBe("හෙලෝ JARVIS");
  });
});

