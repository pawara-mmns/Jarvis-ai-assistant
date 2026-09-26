import { create } from "zustand";
import type { AssistantState } from "@shared/types/assistant-state";

export interface AssistantUiState {
  state: AssistantState;
  transcript: string;
  responseText: string;
  executionLabel?: string;
  errorMessage?: string;
  setState(state: AssistantState): void;
  setTranscript(transcript: string): void;
  setResponseText(responseText: string): void;
  setExecutionLabel(executionLabel?: string): void;
  setErrorMessage(errorMessage?: string): void;
}

export const assistantUiInitialState = {
  state: "idle" as AssistantState,
  transcript: "Open VS Code and start my project.",
  responseText: "Preparing your development environment.",
  executionLabel: undefined,
  errorMessage: undefined,
};

export const useAssistantUiStore = create<AssistantUiState>((set) => ({
  ...assistantUiInitialState,
  setState: (state) => set({ state }),
  setTranscript: (transcript) => set({ transcript }),
  setResponseText: (responseText) => set({ responseText }),
  setExecutionLabel: (executionLabel) => set({ executionLabel }),
  setErrorMessage: (errorMessage) => set({ errorMessage }),
}));
