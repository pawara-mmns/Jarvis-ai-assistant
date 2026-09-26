# JARVIS Desktop AI

Phase 4.1 adds trusted-root folder indexing and cached Start Menu application discovery to the seven schema-validated Windows desktop tools. Gemini requests friendly names; Python resolves, validates, and executes only approved local targets.

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

The agent binds only to `127.0.0.1`. Gemini credentials stay in Python. There is no arbitrary shell, command, executable-path, mouse, or keyboard access. See `docs/CURRENT_STATE.md`, `docs/GEMINI.md`, and `docs/TOOLS.md`.
