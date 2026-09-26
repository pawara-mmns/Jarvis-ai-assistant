import { useConnectionStore } from "../../stores/connection-store";

const connectionLabels = {
  connecting: "Connecting",
  connected: "Connected",
  offline: "Offline",
} as const;

export function ConnectionStatus() {
  const { status, checkConnection } = useConnectionStore();

  return (
    <div className="connection-status" aria-label="System connectivity">
      <span className="connection-item">
        <span className="status-dot status-dot--ready" aria-hidden="true" />
        <span className="connection-name">Desktop</span>
        <span>Ready</span>
      </span>
      <button
        type="button"
        className="connection-item connection-action"
        onClick={() => void checkConnection()}
        aria-label={`Agent ${connectionLabels[status]}. Retry connection`}
        title="Retry agent connection"
      >
        <span className={`status-dot status-dot--${status}`} aria-hidden="true" />
        <span className="connection-name">Agent</span>
        <span>{connectionLabels[status]}</span>
      </button>
    </div>
  );
}
