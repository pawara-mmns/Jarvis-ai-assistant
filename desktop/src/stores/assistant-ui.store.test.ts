import { beforeEach, describe, expect, it } from "vitest";
import { assistantUiInitialState, useAssistantUiStore } from "./assistant-ui.store";

describe("assistant UI store", () => {
  beforeEach(() => {
    useAssistantUiStore.setState(assistantUiInitialState);
  });

  it("updates state and current interaction content", () => {
    const store = useAssistantUiStore.getState();

    store.setState("executing");
    store.setTranscript("Open the project.");
    store.setResponseText("I will prepare the workspace.");
    store.setExecutionLabel("Launching development environment...");

    expect(useAssistantUiStore.getState()).toMatchObject({
      state: "executing",
      transcript: "Open the project.",
      responseText: "I will prepare the workspace.",
      executionLabel: "Launching development environment...",
    });
  });

  it("records a visible error message", () => {
    useAssistantUiStore.getState().setErrorMessage("The simulated action could not continue.");

    expect(useAssistantUiStore.getState().errorMessage).toContain("could not continue");
  });
});
