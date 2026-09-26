import { useConnectionStore } from "../../stores/connection-store";
import { liveConversationController } from "../../live/LiveConversationController";
import { useLiveStore, type AiConnectionState } from "../../stores/live.store";

const connectionLabels = {
  connecting: "Connecting",
  connected: "Connected",
  offline: "Offline",
} as const;

const aiLabels: Record<AiConnectionState, string> = {
  disconnected: "Offline",
  connecting: "Connecting",
  ready: "Ready",
  active: "Ready",
  closing: "Closing",
  error: "Error",
  not_configured: "Not Configured",
};

const aiDotStates: Record<AiConnectionState, string> = {
  disconnected: "offline",
  connecting: "connecting",
  ready: "ready",
  active: "ready",
  closing: "connecting",
  error: "error",
  not_configured: "error",
};

export function ConnectionStatus() {
  const { status, checkConnection } = useConnectionStore();
  const aiState = useLiveStore((store) => store.connectionState);
  const aiError = useLiveStore((store) => store.error);
  const aiConnected = aiState === "ready" || aiState === "active";

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
      <button
        type="button"
        className="connection-item connection-action"
        onClick={() =>
          aiConnected ? liveConversationController.disconnect() : void liveConversationController.connect()
        }
        disabled={aiState === "connecting" || aiState === "closing"}
        aria-label={`AI ${aiLabels[aiState]}. ${aiConnected ? "Disconnect" : "Connect AI"}`}
        title={aiError ?? (aiConnected ? "Disconnect AI" : "Connect AI")}
      >
        <span className={`status-dot status-dot--${aiDotStates[aiState]}`} aria-hidden="true" />
        <span className="connection-name">AI</span>
        <span>{aiLabels[aiState]}</span>
        <span className="ai-action-label">{aiConnected ? "Disconnect" : "Connect"}</span>
      </button>
    </div>
  );
}
