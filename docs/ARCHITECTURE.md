# Architecture

## Phase 4.1 Runtime

```text
Microphone → renderer PCM/VAD → authenticated localhost WebSocket
  → GeminiLiveService → long-lived gemini-3.8-live session

Gemini FunctionCall
  → ToolRegistry lookup → Pydantic argument validation → permission check
  → FolderResolver/AppResolver → trusted cached discovery → ambiguity/security checks
  → approved Windows tool → timeout/exception boundary → ToolResult
  → Gemini FunctionResponse with matching call ID → concise spoken result

Gemini audio/transcripts + tool lifecycle
  → typed WebSocket events → playback/current interaction/executing UI
```

Electron main still owns the secure window, audio-only permission policy, Python lifecycle, backend port, and ephemeral bridge token. The sandboxed renderer has no Node, filesystem, process, raw IPC, or Gemini credential access. Python owns the Gemini key, Live session, `ToolRegistry`, and Windows adapter.

## Local Interfaces

- `GET /health` remains the narrow health contract.
- `/ws/live` accepts only `session.start`, `audio.chunk`, `audio.end`, and `session.stop`; there is no execution endpoint.
- Server messages add typed `tool.started`, `tool.completed`, and `tool.failed` events. Raw tool arguments and paths are not sent to the renderer.
- FastAPI binds exclusively to `127.0.0.1`; each app launch uses an ephemeral authenticated bridge token.

Folder discovery indexes directory names only under bounded trusted roots. Application discovery checks fixed trusted definitions and `.lnk` files under the user/system Start Menu. Neither resolver performs a full-drive scan or exposes its index to Gemini.

One explicit AI connection maps to one Gemini client/session across voice and tool turns. Desktop actions are synchronous/blocking declarations and execute sequentially. See [TOOLS.md](TOOLS.md) and [RESOLUTION.md](RESOLUTION.md).
