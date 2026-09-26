import { useEffect } from "react";
import { AppShell } from "./components/AppShell/AppShell";
import { AssistantStatus } from "./components/AssistantStatus/AssistantStatus";
import { BottomStatus } from "./components/BottomStatus/BottomStatus";
import { DevStateSimulator } from "./components/DevStateSimulator/DevStateSimulator";
import { MiniAssistant } from "./components/MiniAssistant/MiniAssistant";
import { TranscriptPanel } from "./components/TranscriptPanel/TranscriptPanel";
import { VoiceOrb } from "./components/VoiceOrb/VoiceOrb";
import { Waveform } from "./components/Waveform/Waveform";
import { assistantStateConfig } from "./config/assistant-state.config";
import { useAssistantUiStore } from "./stores/assistant-ui.store";
import { useConnectionStore } from "./stores/connection-store";

export default function App() {
  const checkConnection = useConnectionStore((store) => store.checkConnection);
  const { state, transcript, responseText, executionLabel, errorMessage } = useAssistantUiStore();
  const stateConfig = assistantStateConfig[state];

  useEffect(() => {
    void checkConnection();
  }, [checkConnection]);

  return (
    <AppShell
      footer={<BottomStatus />}
      developmentTools={import.meta.env.DEV ? <DevStateSimulator /> : undefined}
    >
      <main className={`main-stage main-stage--${state}`} data-assistant-state={state}>
        <div className="stage-metadata" aria-hidden="true">
          <span>VOICE INTERFACE</span>
          <span>UI / 0.2.0</span>
        </div>

        <section className="focus-stage" aria-label="Assistant voice status">
          <div className="orb-frame">
            <span className="orb-coordinate orb-coordinate--top">J-01</span>
            <span className="orb-coordinate orb-coordinate--side">{stateConfig.activity}</span>
            <VoiceOrb state={state} intensity={stateConfig.intensity} />
          </div>
          <Waveform mode={state} />
          <AssistantStatus state={state} executionLabel={executionLabel} />
        </section>

        <aside className="context-rail">
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
