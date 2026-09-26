export type MicrophonePermissionState =
  | "unknown"
  | "prompt"
  | "granted"
  | "denied"
  | "unavailable";

export type AudioEngineStatus = "idle" | "starting" | "active" | "error";

export interface AudioInputDevice {
  deviceId: string;
  label: string;
}

export interface AudioMetrics {
  audioLevel: number;
  waveformLevels: readonly number[];
  speechDetected: boolean;
}

export interface AudioEngineSnapshot extends AudioMetrics {
  status: AudioEngineStatus;
  permissionState: MicrophonePermissionState;
  selectedDeviceId?: string;
  devices: readonly AudioInputDevice[];
  error?: string;
}

export interface AudioFrame {
  /** Continuous transient microphone samples. Consumers must copy them if retained. */
  samples: Float32Array;
  sampleRate: number;
  timestamp: number;
}

export type AudioSnapshotListener = (snapshot: AudioEngineSnapshot) => void;
export type AudioFrameListener = (frame: AudioFrame) => void;
