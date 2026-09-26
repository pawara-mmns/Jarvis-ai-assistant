import { useEffect } from "react";
import { AppShell } from "./components/AppShell/AppShell";
import { AssistantStatus } from "./components/AssistantStatus/AssistantStatus";
import { BottomStatus } from "./components/BottomStatus/BottomStatus";
import { DevStateSimulator } from "./components/DevStateSimulator/DevStateSimulator";
import { MiniAssistant } from "./components/MiniAssistant/MiniAssistant";
import { MicrophoneControls } from "./components/MicrophoneControls/MicrophoneControls";
import { TranscriptPanel } from "./components/TranscriptPanel/TranscriptPanel";
import { VoiceOrb } from "./components/VoiceOrb/VoiceOrb";
import { Waveform } from "./components/Waveform/Waveform";
import { assistantStateConfig } from "./config/assistant-state.config";
import { resolveAudioDrivenState } from "./audio/state-integration";
import {
  disposeAudioImmediately,
  initializeAudioStore,
  scheduleAudioStoreDisposal,
  useAudioStore,
} from "./stores/audio.store";
import { useAssistantUiStore } from "./stores/assistant-ui.store";
import { useConnectionStore } from "./stores/connection-store";
import { liveConversationController } from "./live/LiveConversationController";
import { useLiveStore } from "./stores/live.store";

export default function App() {
  const checkConnection = useConnectionStore((store) => store.checkConnection);
  const {
    state,
    inputSource,
    transcript,
    responseText,
    executionLabel,
    errorMessage,
    setState,
  } = useAssistantUiStore();
  const audioStatus = useAudioStore((store) => store.status);
  const audioLevel = useAudioStore((store) => store.audioLevel);
  const waveformLevels = useAudioStore((store) => store.waveformLevels);
  const speechDetected = useAudioStore((store) => store.speechDetected);
  const aiConnectionState = useLiveStore((store) => store.connectionState);
  const outputLevel = useLiveStore((store) => store.outputLevel);
  const outputWaveformLevels = useLiveStore((store) => store.outputWaveformLevels);
  const stateConfig = assistantStateConfig[state];
  const microphoneActive = inputSource === "microphone" && audioStatus === "active";
  const aiSessionActive = aiConnectionState === "ready" || aiConnectionState === "active";
  const speakingFromGemini = state === "speaking" && aiSessionActive;

  useEffect(() => {
    void checkConnection();
  }, [checkConnection]);

  useEffect(() => {
    void initializeAudioStore();
    liveConversationController.initialize();
    window.addEventListener("beforeunload", disposeAudioImmediately);
    const disposeLive = () => liveConversationController.dispose();
    window.addEventListener("beforeunload", disposeLive);
    return () => {
      window.removeEventListener("beforeunload", disposeAudioImmediately);
      window.removeEventListener("beforeunload", disposeLive);
      liveConversationController.dispose();
      scheduleAudioStoreDisposal();
    };
  }, []);

  useEffect(() => {
    if (inputSource !== "microphone" || aiConnectionState !== "disconnected") return;
    const nextState = resolveAudioDrivenState(state, microphoneActive, speechDetected);
    if (nextState !== state) setState(nextState);
  }, [aiConnectionState, inputSource, microphoneActive, setState, speechDetected, state]);

  return (
    <AppShell
      footer={<BottomStatus />}
      developmentTools={import.meta.env.DEV ? <DevStateSimulator /> : undefined}
    >
      <main className={`main-stage main-stage--${state}`} data-assistant-state={state}>
        <div className="stage-metadata" aria-hidden="true">
          <span>VOICE INTERFACE</span>
          <span>LIVE TOOLS / 0.5.1</span>
        </div>

        <section className="focus-stage" aria-label="Assistant voice status">
          <div className="orb-frame">
            <span className="orb-coordinate orb-coordinate--top">J-01</span>
            <span className="orb-coordinate orb-coordinate--side">{stateConfig.activity}</span>
            <VoiceOrb
              state={state}
              intensity={
                speakingFromGemini
                  ? Math.max(0.1, outputLevel)
                  : microphoneActive
                    ? Math.max(0.1, audioLevel)
                    : stateConfig.intensity
              }
            />
          </div>
          <Waveform
            mode={state}
            levels={
              speakingFromGemini
                ? outputWaveformLevels
                : microphoneActive
                  ? waveformLevels
                  : undefined
            }
          />
          <AssistantStatus state={state} executionLabel={executionLabel} />
        </section>

        <aside className="context-rail">
          <MicrophoneControls />
          <TranscriptPanel
            transcript={transcript}
            responseText={responseText}
            executionLabel={executionLabel}
            errorMessage={errorMessage}
          />
          <MiniAssistant state={state} />
        </aside>
      </main>
    </AppShell>
  );
}
