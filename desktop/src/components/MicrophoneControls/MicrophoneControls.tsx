import { useAudioStore } from "../../stores/audio.store";
import { useAssistantUiStore } from "../../stores/assistant-ui.store";
import { liveConversationController } from "../../live/LiveConversationController";
import { useLiveStore } from "../../stores/live.store";

const permissionLabels = {
  unknown: "Permission not requested",
  prompt: "Permission required",
  granted: "Local access granted",
  denied: "Permission denied",
  unavailable: "Capture unavailable",
} as const;

export function MicrophoneControls() {
  const status = useAudioStore((store) => store.status);
  const permissionState = useAudioStore((store) => store.permissionState);
  const devices = useAudioStore((store) => store.devices);
  const selectedDeviceId = useAudioStore((store) => store.selectedDeviceId);
  const speechDetected = useAudioStore((store) => store.speechDetected);
  const error = useAudioStore((store) => store.error);
  const startMicrophone = useAudioStore((store) => store.startMicrophone);
  const stopMicrophone = useAudioStore((store) => store.stopMicrophone);
  const selectDevice = useAudioStore((store) => store.selectDevice);
  const setInputSource = useAssistantUiStore((store) => store.setInputSource);
  const aiState = useLiveStore((store) => store.connectionState);
  const aiSessionActive = aiState === "ready" || aiState === "active";

  const isActive = status === "active";
  const statusLabel =
    status === "starting"
      ? "MIC REQUESTING"
      : status === "error"
        ? "MIC ERROR"
        : isActive && speechDetected
          ? "SPEECH DETECTED"
          : isActive
            ? "MIC ACTIVE"
            : "MIC OFF";

  const toggleMicrophone = async () => {
    setInputSource("microphone");
    if (isActive) {
      liveConversationController.disconnect();
      await stopMicrophone();
    }
    else await startMicrophone();
  };

  return (
    <section className={`microphone-panel microphone-panel--${status}`} aria-label="Microphone controls">
      <div className="microphone-panel__status" aria-live="polite">
        <span className="microphone-signal" aria-hidden="true" />
        <div>
          <strong>{statusLabel}</strong>
          <span>{error ?? permissionLabels[permissionState]}</span>
        </div>
        <button
          type="button"
          className="microphone-toggle"
          onClick={() => void toggleMicrophone()}
          disabled={status === "starting" || permissionState === "unavailable"}
          aria-pressed={isActive}
          aria-label={isActive ? "Disable microphone" : "Enable microphone"}
        >
          {isActive ? "Disable" : status === "starting" ? "Requesting" : "Enable"}
        </button>
      </div>

      <label className="microphone-device">
        <span>Input device</span>
        <select
          value={selectedDeviceId ?? ""}
          onChange={(event) => void selectDevice(event.target.value)}
          disabled={status === "starting" || devices.length === 0}
          aria-label="Microphone input device"
        >
          <option value="">System default</option>
          {devices.map((device, index) => (
            <option value={device.deviceId} key={device.deviceId || `microphone-${index}`}>
              {device.label || `Microphone ${index + 1}`}
            </option>
          ))}
        </select>
      </label>
      <p className={`microphone-privacy${aiSessionActive ? " microphone-privacy--live" : ""}`}>
        {aiSessionActive
          ? "AI SESSION ACTIVE · detected speech is sent to Gemini"
          : "LOCAL ONLY · audio stays on this device"}
      </p>
    </section>
  );
}
