# Security Foundation

- Apply least privilege at every boundary.
- The renderer runs with `contextIsolation: true`, `nodeIntegration: false`, and Electron sandboxing enabled.
- Preload exposes narrow, allowlisted functions rather than raw IPC.
- The Python backend binds only to `127.0.0.1`.
- No arbitrary shell, process, or filesystem API is exposed to the renderer or agent.
- Future tools must live in an explicit registry with schemas and policy checks.
- Destructive actions will require clear user confirmation before execution.
- Secrets must not be committed or unnecessarily exposed to the renderer.
- Gemini will never receive unrestricted OS access. It may only request approved local tools, which local policy code controls.

Phase 0 exposes only the health endpoint and contains no AI-triggered actions.
