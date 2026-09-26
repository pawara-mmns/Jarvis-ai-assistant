import { create } from "zustand";
import type { AssistantState } from "@shared/types/assistant-state";

export type AssistantInputSource = "microphone" | "simulator";

export interface AssistantUiState {
  state: AssistantState;
  inputSource: AssistantInputSource;
  transcript: string;
  responseText: string;
  executionLabel?: string;
  errorMessage?: string;
  setState(state: AssistantState): void;
  setInputSource(inputSource: AssistantInputSource): void;
  setTranscript(transcript: string): void;
  setResponseText(responseText: string): void;
  setExecutionLabel(executionLabel?: string): void;
  setErrorMessage(errorMessage?: string): void;
}

export const assistantUiInitialState = {
  state: "idle" as AssistantState,
  inputSource: "microphone" as AssistantInputSource,
  transcript: "Open VS Code and start my project.",
  responseText: "Preparing your development environment.",
  executionLabel: undefined,
  errorMessage: undefined,
};

export const useAssistantUiStore = create<AssistantUiState>((set) => ({
  ...assistantUiInitialState,
  setState: (state) => set({ state }),
  setInputSource: (inputSource) => set({ inputSource }),
  setTranscript: (transcript) => set({ transcript }),
  setResponseText: (responseText) => set({ responseText }),
  setExecutionLabel: (executionLabel) => set({ executionLabel }),
  setErrorMessage: (errorMessage) => set({ errorMessage }),
}));
