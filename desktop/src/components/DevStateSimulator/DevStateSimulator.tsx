import type { AssistantState } from "@shared/types/assistant-state";
import { assistantStateConfig, assistantStates } from "../../config/assistant-state.config";
import { useAssistantUiStore } from "../../stores/assistant-ui.store";

interface DemoContent {
  transcript: string;
  responseText: string;
  executionLabel?: string;
  errorMessage?: string;
}

const demoContent: Record<AssistantState, DemoContent> = {
  sleeping: { transcript: "", responseText: "Low-power standby active." },
  idle: {
    transcript: "Open VS Code and start my project.",
    responseText: "Preparing your development environment.",
  },
  listening: {
    transcript: "Open Chrome and search for JavaScript tutorials",
    responseText: "I am listening.",
  },
  thinking: {
    transcript: "Summarize the current project architecture.",
    responseText: "Reviewing the relevant project context.",
  },
  executing: {
    transcript: "Open the development workspace.",
    responseText: "Preparing the requested environment.",
    executionLabel: "Launching development environment...",
  },
  speaking: {
    transcript: "What is the current system status?",
    responseText: "All Phase 1 interface systems are responding normally.",
  },
  confirmation: {
    transcript: "Continue with the simulated action.",
    responseText: "This action requires your confirmation before it can continue.",
  },
  error: {
    transcript: "Retry the previous simulated action.",
    responseText: "I could not complete that request.",
    errorMessage: "The simulated service did not respond. No system action was performed.",
  },
};

export function DevStateSimulator() {
  const store = useAssistantUiStore();

  const selectState = (state: AssistantState) => {
    const demo = demoContent[state];
    store.setState(state);
    store.setTranscript(demo.transcript);
    store.setResponseText(demo.responseText);
    store.setExecutionLabel(demo.executionLabel);
    store.setErrorMessage(demo.errorMessage);
  };

  return (
    <aside className="dev-simulator" aria-label="Development state simulator">
      <div className="dev-simulator__header">
        <span className="dev-badge">DEV</span>
        <span>State simulator</span>
      </div>
      <div className="dev-state-controls" role="group" aria-label="Select assistant state">
        {assistantStates.map((state) => (
          <button
            type="button"
            key={state}
            className={store.state === state ? "is-active" : undefined}
            aria-pressed={store.state === state}
            onClick={() => selectState(state)}
          >
            {assistantStateConfig[state].shortLabel}
          </button>
        ))}
      </div>
      <details className="dev-copy-controls">
        <summary>Edit mock interaction</summary>
        <div className="dev-copy-grid">
          <label>
            Transcript
            <textarea
              value={store.transcript}
              onChange={(event) => store.setTranscript(event.target.value)}
              rows={2}
            />
          </label>
          <label>
            Assistant
            <textarea
              value={store.responseText}
              onChange={(event) => store.setResponseText(event.target.value)}
              rows={2}
            />
          </label>
          <label>
            Execution
            <input
              value={store.executionLabel ?? ""}
              onChange={(event) => store.setExecutionLabel(event.target.value || undefined)}
            />
          </label>
        </div>
      </details>
    </aside>
  );
}
