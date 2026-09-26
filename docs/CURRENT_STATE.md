# Current State

**Version:** 0.1.0  
**Current Phase:** Phase 0 — Foundation

## Completed

- Electron + Vite + React + strict TypeScript desktop shell
- Tailwind-based temporary connection status screen
- Isolated preload bridge with one typed health API
- FastAPI agent restricted to `127.0.0.1`
- Electron-managed Python startup, readiness polling, logs, and shutdown
- Shared Zod health contract and TypeScript assistant state type
- Matching Python assistant state enum and Pydantic health response
- Vitest contract/service parsing tests and pytest endpoint/schema tests
- Environment example, Windows-compatible Python setup helpers, and architecture docs

## Architecture

The renderer calls `window.jarvis.getBackendHealth()`. Preload invokes an allowlisted Electron IPC channel. Electron main requests the agent's `GET /health` endpoint and validates its response. `BackendManager` is the sole owner of the Python child process.

## How to Run

```powershell
npm install
npm run python:setup
npm run dev
```

Verification commands are `npm run typecheck`, `npm run test`, `npm run test:python`, and `npm run build`.

## Known Issues

- Development requires a local Python 3.12+ installation; a packaged Python runtime is not part of Phase 0.
- The development UI reports a generic offline state; detailed diagnostics remain in Electron logs.
- Production installer and executable bundling are deferred to Phase 10.

## Next Phase

Phase 1 — Voice Reactive UI. It is documented but not implemented.
