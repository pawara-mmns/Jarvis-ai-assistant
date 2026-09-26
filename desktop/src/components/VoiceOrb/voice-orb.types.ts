import type { AssistantState } from "@shared/types/assistant-state";

export interface VoiceOrbProps {
  state: AssistantState;
  intensity?: number;
  size?: "main" | "mini";
}
