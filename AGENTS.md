# JARVIS Desktop AI

JARVIS is a Windows desktop AI assistant. Phase 1 adds the voice-reactive UI foundation to the secure Electron/React shell and localhost FastAPI agent.

## Architecture

Renderer → narrow preload IPC API → Electron main → HTTP on `127.0.0.1` → Python agent.

Electron main owns privileged operations and the Python lifecycle. Never expose Node, arbitrary IPC, shell execution, or filesystem access to the renderer.

## Working Principles

- Work only on the phase explicitly requested.
- Keep TypeScript strict and modules small; avoid `any`.
- Validate data crossing process boundaries.
- Bind backend services to `127.0.0.1` only.
- Never commit secrets or expose them to the renderer.
- Read only task-relevant documentation and files.
- Update `docs/CURRENT_STATE.md` after significant changes.

## Commands

- `npm install` — install desktop dependencies
- `npm run python:setup` — create `.venv` and install Python dependencies
- `npm run dev` — launch the desktop app and managed agent
- `npm run build` / `npm run typecheck` / `npm run test` / `npm run test:python`

All relevant checks must pass before handoff.

## Documentation Map

- Architecture → `docs/ARCHITECTURE.md`
- Current implementation → `docs/CURRENT_STATE.md`
- Roadmap → `docs/PHASES.md`
- UI → `docs/UI.md`
- Gemini design → `docs/GEMINI.md`
- Security and tool permissions → `docs/SECURITY.md`
