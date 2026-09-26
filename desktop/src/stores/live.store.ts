import { create } from "zustand";

export type AiConnectionState =
  | "disconnected"
  | "connecting"
  | "ready"
  | "active"
  | "closing"
  | "error"
  | "not_configured";

export type OutputPlaybackState = "idle" | "playing" | "error";

export interface LiveUiState {
  connectionState: AiConnectionState;
  inputSampleRate?: number;
  streaming: boolean;
  outputPlaybackState: OutputPlaybackState;
  outputLevel: number;
  outputWaveformLevels: readonly number[];
  error?: string;
  setConnectionState(connectionState: AiConnectionState): void;
  setStreaming(streaming: boolean): void;
  setInputSampleRate(inputSampleRate?: number): void;
  setPlayback(outputPlaybackState: OutputPlaybackState, outputLevel: number, levels: readonly number[]): void;
  setError(error?: string): void;
  reset(): void;
}

const emptyLevels = (): number[] => new Array<number>(24).fill(0);

export const liveUiInitialState = {
  connectionState: "disconnected" as AiConnectionState,
  inputSampleRate: undefined,
  streaming: false,
  outputPlaybackState: "idle" as OutputPlaybackState,
  outputLevel: 0,
  outputWaveformLevels: emptyLevels(),
  error: undefined,
};

export const useLiveStore = create<LiveUiState>((set) => ({
  ...liveUiInitialState,
  setConnectionState: (connectionState) => set({ connectionState }),
  setStreaming: (streaming) => set({ streaming }),
  setInputSampleRate: (inputSampleRate) => set({ inputSampleRate }),
  setPlayback: (outputPlaybackState, outputLevel, outputWaveformLevels) =>
    set({ outputPlaybackState, outputLevel, outputWaveformLevels }),
  setError: (error) => set({ error }),
  reset: () => set({ ...liveUiInitialState, outputWaveformLevels: emptyLevels() }),
}));

