# Architecture

## Runtime Shape

```text
React renderer
    ↓ narrow, typed preload API
Electron IPC handler
    ↓ validated HTTP on 127.0.0.1
Python FastAPI agent
```

The renderer is an untrusted presentation layer. It has no Node integration, process access, filesystem access, or raw Electron IPC. Its only Phase 0 privileged API is `window.jarvis.getBackendHealth()`.

The preload script uses context isolation and exposes that single frozen API. Both the preload boundary and the Electron HTTP client validate the health payload with the shared Zod schema.

Electron main is the desktop trust boundary. It creates the window, registers the allowlisted IPC handler, and owns `BackendManager`. The manager selects a Python interpreter, starts one child process, forwards concise logs, polls readiness, and performs graceful shutdown with a forced fallback.

The FastAPI agent is a separate local process. Configuration enforces `127.0.0.1`; Phase 0 exposes only `GET /health`. Pydantic defines the response contract. Empty domain packages reserve clear locations for later AI, audio, tools, security, and memory work without implementing it.

## Source Boundaries

- `desktop/electron/`: privileged Electron main/preload code and lifecycle management
- `desktop/src/`: unprivileged React UI
- `agent/`: local Python service
- `shared/`: TypeScript schemas, IPC names, and domain types
- `docs/`: compact architecture and roadmap context

## Future Direction

Later phases may add realtime transport, Gemini-mediated reasoning, audio, and an approved tool registry. Gemini will remain outside the OS trust boundary: models may propose allowlisted tool calls, while local policy code validates and executes them.
