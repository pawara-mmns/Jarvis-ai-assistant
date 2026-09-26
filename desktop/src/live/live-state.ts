import type { AssistantState } from "@shared/types/assistant-state";

export type LiveTurnEvent =
  | "speech.started"
  | "speech.ended"
  | "output.started"
  | "output.completed"
  | "failed";

export function resolveLiveAssistantState(event: LiveTurnEvent): AssistantState {
  switch (event) {
    case "speech.started":
      return "listening";
    case "speech.ended":
      return "thinking";
    case "output.started":
      return "speaking";
    case "output.completed":
      return "idle";
    case "failed":
      return "error";
  }
}

