# Security Foundation

- Electron keeps context isolation, renderer sandboxing, and audio-only media permissions.
- Python binds only to `127.0.0.1`; the typed Live WebSocket requires an ephemeral bridge token.
- `GEMINI_API_KEY` stays in Python and never appears in preload, renderer messages, UI, or logs.
- Gemini can request only seven registered functions. There is no shell, command, code, arbitrary executable-path, generic executor, or `/execute` endpoint.
- Every request passes through schema validation, `SAFE`/`CONFIRM`/`BLOCKED` classification, a timeout, and an exception-sanitizing `ToolResult` boundary.
- App names resolve only through fixed executable candidates, validated logical aliases, or shortcuts physically contained under trusted Start Menu roots. No Gemini text is interpolated into a command, and process launch uses `shell=False`.
- URLs allow only absolute HTTP(S) schemes; search text is URL encoded.
- Folder discovery indexes names and relative parent context only under known or configured roots, to a bounded depth. It never scans whole drives or file contents.
- Explicit folder paths are canonicalized and must remain inside a trusted root or exactly match a configured alias target. Relative traversal and system/outside-root paths are rejected.
- Folder access opens only an existing directory and never creates, deletes, moves, renames, or returns its absolute path to Gemini.
- Volume control targets the default output endpoint only.
- Active-window output is limited to application name and a bounded title; it never captures contents, process paths, or keystrokes.
- Screenshots are written locally under the user's Pictures/JARVIS/Screenshots folder. Image bytes and absolute paths are never sent to Gemini.
- Tool audit logs contain timestamp, tool name, success, and duration—not arguments or sensitive paths.
- Calls execute sequentially with a maximum of five per user turn.

`CONFIRM` exists for future policy work but Phase 4 exposes no confirmable or destructive tools. Arbitrary shell execution remains blocked by absence, not merely by prompting.
