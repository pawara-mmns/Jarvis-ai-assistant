import { useEffect } from "react";
import { StatusRow } from "./components/StatusRow";
import { useConnectionStore } from "./stores/connection-store";

const statusLabels = {
  connecting: "Connecting...",
  connected: "Connected",
  offline: "Offline",
} as const;

export default function App() {
  const { status, health, checkConnection } = useConnectionStore();

  useEffect(() => {
    void checkConnection();
  }, [checkConnection]);

  return (
    <main className="flex min-h-screen items-center justify-center bg-canvas px-6 text-slate-100">
      <section className="w-full max-w-md rounded-2xl border border-slate-800 bg-panel p-8 shadow-2xl shadow-black/40">
        <div className="mb-8">
          <p className="mb-2 text-xs font-semibold uppercase tracking-[0.28em] text-cyan-300">
            Phase 0 — Foundation
          </p>
          <h1 className="text-3xl font-semibold tracking-tight">JARVIS Desktop AI</h1>
          <p className="mt-3 text-sm leading-6 text-slate-400">
            Secure desktop shell and local agent foundation.
          </p>
        </div>

        <div className="rounded-xl border border-slate-800 bg-black/20 px-4">
          <StatusRow label="Desktop" value="Ready" active />
          <StatusRow label="Agent" value={statusLabels[status]} active={status === "connected"} />
          {health ? <StatusRow label="Service" value={health.service} /> : null}
          {health ? <StatusRow label="Version" value={health.version} /> : null}
        </div>

        <button
          type="button"
          onClick={() => void checkConnection()}
          disabled={status === "connecting"}
          className="mt-6 w-full rounded-lg border border-cyan-900 bg-cyan-950/40 px-4 py-3 text-sm font-medium text-cyan-200 transition hover:border-cyan-700 hover:bg-cyan-950/70 disabled:cursor-wait disabled:opacity-60"
        >
          Retry Connection
        </button>
      </section>
    </main>
  );
}
