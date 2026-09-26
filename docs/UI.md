# UI Architecture

Phase 3 preserves the Phase 1 HUD and Phase 2 microphone controls.

- The header adds a restrained AI item: Offline, Connecting, Ready, Error, or Not Configured, plus Connect/Disconnect.
- The microphone panel explicitly says either `LOCAL ONLY · audio stays on this device` or `AI SESSION ACTIVE · detected speech is sent to Gemini`.
- `CURRENT INTERACTION` remains a two-row, current-turn view. Gemini input transcription replaces `YOU`; output transcription replaces `JARVIS`. It is not a chat history.
- Listening uses microphone amplitude and waveform. Speaking uses actual decoded Gemini PCM amplitude and waveform.
- Normal Live voice states are idle, listening, thinking, speaking, and error. `executing` remains reserved for future tools.
- The development strip shows only connection state, input sample rate, input streaming/local state, and output playback state—never keys, base64 audio, or large event logs.

Local VAD still controls idle/listening when AI is disconnected. While a Live session is active, the Live controller owns the turn state so playback and turn-completion timing remain authoritative.
