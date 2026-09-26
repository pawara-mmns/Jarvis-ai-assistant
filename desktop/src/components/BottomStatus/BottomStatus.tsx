import { useConnectionStore } from "../../stores/connection-store";

export function BottomStatus() {
  const { status, health } = useConnectionStore();

  return (
    <footer className="bottom-status">
      <div className="bottom-status__group">
        <span>Desktop</span>
        <strong>Ready</strong>
      </div>
      <div className="bottom-status__group">
        <span>Agent</span>
        <strong>{status === "connected" ? health?.service : status}</strong>
      </div>
      <div className="bottom-status__group bottom-status__group--end">
        <span>Build</span>
        <strong>Phase 3 · Gemini Live voice</strong>
      </div>
    </footer>
  );
}
