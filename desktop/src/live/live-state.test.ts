import { describe, expect, it } from "vitest";
import { resolveLiveAssistantState } from "./live-state";

describe("Live voice assistant states", () => {
  it("moves through a normal voice turn", () => {
    expect(
      ["speech.started", "speech.ended", "output.started", "output.completed"].map((event) =>
        resolveLiveAssistantState(event as Parameters<typeof resolveLiveAssistantState>[0]),
      ),
    ).toEqual(["listening", "thinking", "speaking", "idle"]);
  });
});

