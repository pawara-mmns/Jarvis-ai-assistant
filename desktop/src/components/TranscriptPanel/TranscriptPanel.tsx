interface TranscriptPanelProps {
  transcript: string;
  responseText: string;
  executionLabel?: string;
  errorMessage?: string;
}

export function TranscriptPanel({
  transcript,
  responseText,
  executionLabel,
  errorMessage,
}: TranscriptPanelProps) {
  return (
    <section className="transcript-panel" aria-label="Current interaction">
      <div className="section-heading">
        <span>Current interaction</span>
        <span className="section-index">01</span>
      </div>

      <div className="interaction-copy">
        <div className="interaction-block">
          <p className="speaker-label">You</p>
          <p className="interaction-text interaction-text--user">
            {transcript || "No voice input captured."}
          </p>
        </div>
        <div className="interaction-rule" aria-hidden="true" />
        <div className="interaction-block">
          <p className="speaker-label speaker-label--assistant">JARVIS</p>
          <p className="interaction-text">{responseText || "Ready when you are."}</p>
        </div>
      </div>

      {executionLabel ? (
        <p className="system-message system-message--execution">
          <span aria-hidden="true" />
          {executionLabel}
        </p>
      ) : null}
      {errorMessage ? (
        <p className="system-message system-message--error" role="alert">
          <span aria-hidden="true" />
          {errorMessage}
        </p>
      ) : null}
    </section>
  );
}
