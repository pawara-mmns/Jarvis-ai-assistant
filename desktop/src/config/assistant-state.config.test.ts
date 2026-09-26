import { describe, expect, it } from "vitest";
import {
  assistantStateConfig,
  assistantStates,
  getAssistantStatusLabel,
} from "./assistant-state.config";

describe("assistant state configuration", () => {
  it("provides UI configuration for every assistant state", () => {
    expect(Object.keys(assistantStateConfig).sort()).toEqual([...assistantStates].sort());
  });

  it.each([
    ["sleeping", "Sleeping"],
    ["idle", "Ready"],
    ["listening", "Listening..."],
    ["thinking", "Thinking..."],
    ["executing", "Executing..."],
    ["speaking", "Speaking..."],
    ["confirmation", "Confirmation required"],
    ["error", "Something went wrong"],
  ] as const)("maps %s to its status label", (state, label) => {
    expect(getAssistantStatusLabel(state)).toBe(label);
  });
});
