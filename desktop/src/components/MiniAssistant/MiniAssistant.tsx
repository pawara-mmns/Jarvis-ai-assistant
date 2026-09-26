import type { AssistantState } from "@shared/types/assistant-state";
import { assistantStateConfig } from "../../config/assistant-state.config";
import { VoiceOrb } from "../VoiceOrb/VoiceOrb";

interface MiniAssistantProps {
  state: AssistantState;
}

export function MiniAssistant({ state }: MiniAssistantProps) {
  return (
    <section className="mini-preview" aria-label="Compact assistant visual preview">
      <div className="section-heading">
        <span>Compact preview</span>
        <span className="section-index">02</span>
      </div>
      <div className="mini-assistant">
        <VoiceOrb state={state} size="mini" />
        <div className="mini-assistant__copy">
          <strong>JARVIS</strong>
          <span>{assistantStateConfig[state].label}</span>
        </div>
        <span className="mini-assistant__signal" aria-hidden="true" />
      </div>
      <p className="mini-preview__note">Visual component preview · window behavior not active</p>
    </section>
  );
}
