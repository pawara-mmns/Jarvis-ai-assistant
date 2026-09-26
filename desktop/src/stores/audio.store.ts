import { create } from "zustand";
import { audioEngine } from "../audio/AudioEngine";
import type {
  AudioEngineStatus,
  AudioInputDevice,
  MicrophonePermissionState,
} from "../audio/audio.types";

interface AudioUiStore {
  status: AudioEngineStatus;
  permissionState: MicrophonePermissionState;
  devices: readonly AudioInputDevice[];
  selectedDeviceId?: string;
  audioLevel: number;
  waveformLevels: readonly number[];
  speechDetected: boolean;
  error?: string;
  startMicrophone(): Promise<void>;
  stopMicrophone(): Promise<void>;
  selectDevice(deviceId: string): Promise<void>;
  refreshDevices(): Promise<void>;
}

const emptyLevels = new Array<number>(24).fill(0);

export const useAudioStore = create<AudioUiStore>((set, get) => ({
  status: "idle",
  permissionState: "unknown",
  devices: [],
  selectedDeviceId: undefined,
  audioLevel: 0,
  waveformLevels: emptyLevels,
  speechDetected: false,
  error: undefined,
  startMicrophone: async () => audioEngine.start(get().selectedDeviceId),
  stopMicrophone: async () => audioEngine.stop(),
  selectDevice: async (deviceId) => audioEngine.switchDevice(deviceId),
  refreshDevices: async () => {
    await audioEngine.getDevices();
  },
}));

let unsubscribe: (() => void) | null = null;
let scheduledDispose: number | null = null;

export async function initializeAudioStore(): Promise<void> {
  if (scheduledDispose !== null) {
    window.clearTimeout(scheduledDispose);
    scheduledDispose = null;
  }
  if (!unsubscribe) {
    unsubscribe = audioEngine.subscribe((snapshot) => {
      useAudioStore.setState({
        status: snapshot.status,
        permissionState: snapshot.permissionState,
        devices: snapshot.devices,
        selectedDeviceId: snapshot.selectedDeviceId,
        audioLevel: snapshot.audioLevel,
        waveformLevels: snapshot.waveformLevels,
        speechDetected: snapshot.speechDetected,
        error: snapshot.error,
      });
    });
  }
  await audioEngine.initialize();
}

export function scheduleAudioStoreDisposal(): void {
  if (scheduledDispose !== null) return;
  scheduledDispose = window.setTimeout(() => {
    scheduledDispose = null;
    unsubscribe?.();
    unsubscribe = null;
    void audioEngine.dispose();
  }, 0);
}

export function disposeAudioImmediately(): void {
  if (scheduledDispose !== null) window.clearTimeout(scheduledDispose);
  scheduledDispose = null;
  unsubscribe?.();
  unsubscribe = null;
  void audioEngine.dispose();
}
