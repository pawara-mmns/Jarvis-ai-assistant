# JARVIS Desktop AI

Phase 3 adds explicitly connected Gemini Live voice to the secure Electron/React desktop shell and localhost FastAPI agent. The existing local microphone UI/VAD resamples detected speech to 16 kHz PCM16; Python owns the Gemini credential and Live session; native PCM output and input/output transcripts return to the HUD.

## Requirements

- Windows 10/11
- Node.js 22+
- Python 3.12+
- A Gemini API key only for Live voice (the app and local microphone work without one)

## Run

```powershell
npm install
npm run python:setup
Copy-Item .env.example .env
# Set GEMINI_API_KEY in .env to enable AI voice.
npm run dev
```

If PowerShell execution policy blocks `npm.ps1`, use `npm.cmd`.

## Verification

```powershell
npm run typecheck
npm run test
npm run build
npm run test:python
```

The agent binds only to `127.0.0.1`. Gemini credentials stay in Python. AI connection is explicit, speech streaming is VAD-gated, and no desktop actions are implemented in Phase 3. See `docs/CURRENT_STATE.md` and `docs/GEMINI.md`.
