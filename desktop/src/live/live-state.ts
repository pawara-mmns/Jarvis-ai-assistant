import type { AssistantState } from "@shared/types/assistant-state";

export type LiveTurnEvent =
  | "speech.started"
  | "speech.ended"
  | "output.started"
  | "output.completed"
  | "tool.started"
  | "tool.completed"
  | "tool.failed"
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
    case "tool.started":
      return "executing";
    case "tool.completed":
    case "tool.failed":
      return "thinking";
    case "failed":
      return "error";
  }
}
