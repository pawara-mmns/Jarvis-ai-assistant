import type { CSSProperties } from "react";
import type { AssistantState } from "@shared/types/assistant-state";
import { assistantStateConfig } from "../../config/assistant-state.config";

interface WaveformProps {
  mode: AssistantState;
  levels?: readonly number[];
}

type WaveStyle = CSSProperties & {
  "--bar-scale": number;
  "--bar-index": number;
};

const simulatedLevels = [
  0.18, 0.32, 0.46, 0.7, 0.42, 0.82, 0.56, 0.34, 0.62, 0.9, 0.48, 0.28, 0.4, 0.76,
  0.58, 0.88, 0.52, 0.3, 0.64, 0.44, 0.72, 0.38, 0.26, 0.16,
] as const;

export function Waveform({ mode, levels }: WaveformProps) {
  const source = levels?.length ? levels : simulatedLevels;
  const energy = assistantStateConfig[mode].waveformEnergy;

  return (
    <div
      className={`waveform waveform--${mode}`}
      role="img"
      aria-label={`${assistantStateConfig[mode].label} activity visualization`}
    >
      <span className="waveform-axis" aria-hidden="true" />
      {source.map((level, index) => (
        <span
          className="waveform-bar"
          key={index}
          aria-hidden="true"
          style={
            {
              "--bar-scale": Math.max(0.08, Math.min(1, level) * energy),
              "--bar-index": index,
            } as WaveStyle
          }
        />
      ))}
    </div>
  );
}
