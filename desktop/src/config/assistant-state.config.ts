import type { AssistantState } from "@shared/types/assistant-state";

export interface AssistantStateConfig {
  label: string;
  shortLabel: string;
  description: string;
  activity: string;
  intensity: number;
  waveformEnergy: number;
  tone: "quiet" | "active" | "warning" | "danger";
}

export const assistantStates = [
  "sleeping",
  "idle",
  "listening",
  "thinking",
  "executing",
  "speaking",
  "confirmation",
  "error",
] as const satisfies readonly AssistantState[];

export const assistantStateConfig: Record<AssistantState, AssistantStateConfig> = {
  sleeping: {
    label: "Sleeping",
    shortLabel: "Sleep",
    description: "Standing by in low-power mode",
    activity: "SYSTEM QUIET",
    intensity: 0.16,
    waveformEnergy: 0.08,
    tone: "quiet",
  },
  idle: {
    label: "Ready",
    shortLabel: "Idle",
    description: "Awaiting your next request",
    activity: "SYSTEM READY",
    intensity: 0.34,
    waveformEnergy: 0.18,
    tone: "quiet",
  },
  listening: {
    label: "Listening...",
    shortLabel: "Listen",
    description: "Voice input channel is active",
    activity: "INPUT ACTIVE",
    intensity: 0.88,
    waveformEnergy: 0.92,
    tone: "active",
  },
  thinking: {
    label: "Thinking...",
    shortLabel: "Think",
    description: "Interpreting the current request",
    activity: "ANALYSIS",
    intensity: 0.62,
    waveformEnergy: 0.42,
    tone: "active",
  },
  executing: {
    label: "Executing...",
    shortLabel: "Execute",
    description: "Coordinating an approved action",
    activity: "ACTION IN PROGRESS",
    intensity: 0.72,
    waveformEnergy: 0.58,
    tone: "active",
  },
  speaking: {
    label: "Speaking...",
    shortLabel: "Speak",
    description: "Delivering the current response",
    activity: "OUTPUT ACTIVE",
    intensity: 0.8,
    waveformEnergy: 0.78,
    tone: "active",
  },
  confirmation: {
    label: "Confirmation required",
    shortLabel: "Confirm",
    description: "Waiting for your explicit approval",
    activity: "ATTENTION",
    intensity: 0.52,
    waveformEnergy: 0.2,
    tone: "warning",
  },
  error: {
    label: "Something went wrong",
    shortLabel: "Error",
    description: "Review the current status and retry",
    activity: "SYSTEM NOTICE",
    intensity: 0.3,
    waveformEnergy: 0.06,
    tone: "danger",
  },
};

export function getAssistantStatusLabel(state: AssistantState): string {
  return assistantStateConfig[state].label;
}
