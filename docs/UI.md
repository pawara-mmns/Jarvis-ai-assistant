# UI Architecture

Phase 4 preserves the voice HUD and activates its existing `executing` state.

- Voice turns remain listening → thinking → speaking → idle.
- A tool call transitions to executing and shows a friendly label such as “Opening Chrome...” or “Setting volume to 40%...”.
- Tool success or failure returns the UI to thinking while the compact action result remains visible and Gemini prepares its grounded spoken response.
- `CURRENT INTERACTION` remains a current-turn view, not chat history or a developer console.
- Typed lifecycle events contain only tool name, friendly label, success, and sanitized message—never raw arguments, paths, stack traces, keys, or audio payloads.
- Tool failure does not force the global error state; connection/transport/playback failures still do.
- Listening and speaking visuals continue to use real microphone/output levels, and barge-in behavior is unchanged.
