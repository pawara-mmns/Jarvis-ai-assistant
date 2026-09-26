import type { AssistantState } from "@shared/types/assistant-state";

const audioInputStates: ReadonlySet<AssistantState> = new Set(["idle", "listening"]);

export function resolveAudioDrivenState(
  currentState: AssistantState,
  microphoneActive: boolean,
  speechDetected: boolean,
): AssistantState {
  if (!audioInputStates.has(currentState)) return currentState;
  if (!microphoneActive) return "idle";
  return speechDetected ? "listening" : "idle";
}
