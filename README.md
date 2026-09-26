# JARVIS Desktop AI

Phase 1 provides the voice-reactive interface foundation for a future Windows desktop AI assistant. It includes a secure Electron shell, state-driven React HUD, managed local FastAPI service, typed IPC/HTTP contracts, UI simulation tools, tests, and architecture documentation. Audio capture, Gemini, and OS automation remain intentionally out of scope.

## Requirements

- Node.js 20 or newer
- Python 3.12 or newer (the Windows `py` launcher is supported)

## Setup

```powershell
npm install
npm run python:setup
```

If Python is installed in a nonstandard location, set `JARVIS_PYTHON_PATH` to the interpreter before running setup. Copy `.env.example` to `.env` only when local configuration changes are needed; `.env` is ignored by Git.

If PowerShell blocks the `npm.ps1` shim under the machine's execution policy, use `npm.cmd` in place of `npm` for the same commands.

## Development

```powershell
npm run dev
```

Electron starts the Python service, waits for `GET /health`, and then opens the React UI. Closing the application stops the service.

To run the backend by itself:

```powershell
npm run dev:agent
```

## Verification

```powershell
npm run typecheck
npm run test
npm run test:python
npm run build
```

See `docs/CURRENT_STATE.md` for the compact implementation summary and known limitations.
