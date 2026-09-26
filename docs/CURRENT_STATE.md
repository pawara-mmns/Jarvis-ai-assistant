# Current State

**Version:** 0.2.0  
**Current Phase:** Phase 1 — Voice Reactive UI Foundation

## Completed

- Phase 0 Electron, React, strict TypeScript, and localhost FastAPI foundation
- Electron-managed Python startup, health validation, and graceful shutdown
- Main JARVIS desktop HUD with restrained responsive styling
- Reusable state-driven `VoiceOrb` and compact orb mode
- Deterministic simulated `Waveform` with a future `levels` input
- Central assistant status and current-interaction transcript panel
- Real desktop and agent connectivity indicators
- Development-only simulator for all eight assistant states and mock copy
- Mini assistant visual preview without additional window behavior
- Reduced-motion behavior and keyboard-accessible controls
- UI configuration, store, status mapping, rendering, contract, and backend tests

## Architecture

The Phase 0 boundary is unchanged: React calls the narrow preload API, Electron main owns IPC and the Python lifecycle, and the agent exposes only localhost health. Phase 1 UI state is local to a small Zustand store and uses the shared `AssistantState` type. UI labels and animation parameters live in one typed configuration.

## How to Run

```powershell
npm install
npm run python:setup
npm run dev
```

If PowerShell blocks `npm.ps1`, use `npm.cmd` in place of `npm`.

Verification commands are `npm run typecheck`, `npm run test`, `npm run test:python`, and `npm run build`.

## Not Yet Implemented

- Microphone or audio capture, VAD, wake word, speech recognition, or speech output
- Gemini or other AI integration
- Desktop tools, OS automation, screen understanding, memory, or routines
- Real floating/always-on-top mini window behavior
- Installer or packaged Python runtime

## Next Phase

Phase 2 — Local Audio Engine.
