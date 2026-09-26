import type { AssistantState } from "@shared/types/assistant-state";
import { assistantStateConfig } from "../../config/assistant-state.config";

interface AssistantStatusProps {
  state: AssistantState;
  executionLabel?: string;
}

export function AssistantStatus({ state, executionLabel }: AssistantStatusProps) {
  const config = assistantStateConfig[state];
  const detail = state === "executing" && executionLabel ? executionLabel : config.description;

  return (
    <div className={`assistant-status assistant-status--${config.tone}`} aria-live="polite">
      <p className="assistant-status__activity">{config.activity}</p>
      <h1>{config.label}</h1>
      <p className="assistant-status__detail">{detail}</p>
    </div>
  );
}
