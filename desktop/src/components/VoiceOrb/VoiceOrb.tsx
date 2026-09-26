import type { CSSProperties } from "react";
import { assistantStateConfig } from "../../config/assistant-state.config";
import type { VoiceOrbProps } from "./voice-orb.types";

type OrbStyle = CSSProperties & { "--orb-intensity": number };

export function VoiceOrb({ state, intensity, size = "main" }: VoiceOrbProps) {
  const config = assistantStateConfig[state];
  const orbIntensity = Math.min(1, Math.max(0, intensity ?? config.intensity));

  return (
    <div
      className={`voice-orb voice-orb--${state} voice-orb--${size}`}
      style={{ "--orb-intensity": orbIntensity } as OrbStyle}
      role="img"
      aria-label={`JARVIS voice indicator: ${config.label}`}
      data-state={state}
    >
      <span className="orb-ambient" aria-hidden="true" />
      <span className="orb-ring orb-ring--outer" aria-hidden="true" />
      <span className="orb-ring orb-ring--inner" aria-hidden="true" />
      <span className="orb-shell" aria-hidden="true">
        <span className="orb-scan" />
        <span className="orb-core" />
        <span className="orb-highlight" />
      </span>
      <span className="orb-state-mark" aria-hidden="true" />
    </div>
  );
}
