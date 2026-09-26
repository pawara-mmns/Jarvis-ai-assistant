# Current State

**Version:** 0.4.0
**Current Phase:** Phase 3 — Gemini Live Voice

## Completed

- Phase 0 secure Electron/React/FastAPI foundation and backend lifecycle
- Phase 1 JARVIS voice-reactive HUD and development simulator
- Phase 2 single-stream microphone engine, device selection, local waveform analysis, and VAD
- Explicit Gemini Live connection and disconnection controls
- Authenticated, typed localhost WebSocket bridge at `/ws/live`
- AudioWorklet-backed continuous microphone frames
- Stateful mono PCM16 resampling to 16 kHz with small chunks and VAD pre-roll
- One backend-owned `gemini-3.8-live` session with finite reconnect/backoff
- Persistent sender/receiver tasks that keep the same Gemini connection open across turns
- Gemini native PCM output queued through Web Audio at its declared sample rate (normally 24 kHz)
- Incremental input and output transcription in the current-interaction UI
- English, Sinhala, and mixed-language behavior in the concise system instruction
- Listening → thinking → speaking → idle state integration and output-driven visuals
- Barge-in playback flushing and Gemini interruption handling
- Missing-key, authentication, transport, conversion, and playback error states
- Mocked backend/frontend Live tests with no paid API calls

## Run

```powershell
npm install
npm run python:setup
Copy-Item .env.example .env
# Add GEMINI_API_KEY to .env for Live voice; the app also runs without it.
npm run dev
```

If PowerShell blocks `npm.ps1`, use `npm.cmd`.

## Not Yet Implemented

- Desktop tool execution or Gemini function calling
- AI/model routing or Gemini Flash planning
- Developer agent or screen vision
- Long-term memory or routines
- Wake word activation
- Production tray, installer, or packaged Python runtime

## Next Phase

Phase 4 — Desktop Tool Engine.
