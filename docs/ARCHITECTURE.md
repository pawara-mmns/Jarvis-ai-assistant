# Architecture

## Phase 3 Runtime

```text
Microphone (one getUserMedia stream)
  ├─ AnalyserNode → RMS / waveform / local VAD → React UI
  └─ AudioWorklet → Float32 → 16 kHz mono PCM16 → VAD gate + pre-roll
       → authenticated ws://127.0.0.1:<port>/ws/live
       → FastAPI route → GeminiLiveService → Google GenAI SDK
       → gemini-3.8-live

Gemini PCM + transcripts
  → GeminiLiveService → typed localhost WebSocket messages
  → AudioPlaybackEngine / current-interaction store
  → speakers + VoiceOrb + Waveform + transcript UI
```

Electron main owns the window, audio-only permission policy, Python lifecycle, backend port, and an ephemeral Live bridge token. Preload exposes only backend health and the local Live connection details. The sandboxed renderer has no Node, filesystem, process, raw IPC, or Gemini credential access.

The renderer owns browser media capture, PCM conversion, VAD gating, and output playback. It never creates a second microphone stream. Python owns `GEMINI_API_KEY`, the official Google GenAI client, the remote Live connection, event translation, and bounded reconnects.

## Local Interfaces

- `GET /health` is the Phase 0 health contract.
- `/ws/live` accepts only `session.start`, `audio.chunk`, `audio.end`, and `session.stop`.
- Server messages are limited to session state, transcripts, PCM output, interruption, turn completion, errors, and close.
- Each application launch uses a random bridge token passed directly from Electron main to its managed Python child and through narrow preload IPC.
- The FastAPI service remains bound exclusively to `127.0.0.1`.

One explicit AI connection maps to one Gemini client/session. Disconnect, renderer unload, Electron quit, WebSocket loss, or backend shutdown closes the session. No desktop tools or generic command transport exist in Phase 3.
