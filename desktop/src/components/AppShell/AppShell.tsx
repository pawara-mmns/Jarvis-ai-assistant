import type { ReactNode } from "react";
import { ConnectionStatus } from "../ConnectionStatus/ConnectionStatus";

interface AppShellProps {
  children: ReactNode;
  footer: ReactNode;
  developmentTools?: ReactNode;
}

export function AppShell({ children, footer, developmentTools }: AppShellProps) {
  return (
    <div className="app-shell">
      <header className="top-bar">
        <div className="brand-lockup" aria-label="JARVIS Desktop AI">
          <span className="brand-mark" aria-hidden="true">
            J
          </span>
          <div>
            <p className="brand-name">JARVIS</p>
            <p className="brand-subtitle">Desktop intelligence system</p>
          </div>
        </div>
        <ConnectionStatus />
      </header>

      {children}
      {footer}
      {developmentTools}
    </div>
  );
}
