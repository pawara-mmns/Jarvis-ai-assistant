# Current State

**Version:** 0.5.1

**Current Phase:** Phase 4.1 — Smart Folder + Application Resolution

## Completed

- Phase 0 — Foundation
- Phase 1 — Voice Reactive UI
- Phase 2 — Local Audio Engine
- Phase 3 — Gemini Live Voice
- Gemini Live manual function calling on the existing long-lived session
- Central safe `ToolRegistry`, schema validation, permissions, timeouts, sanitized results, and audit logs
- Approved application launching, browser URL/search actions, and read-only folder navigation
- Windows output-volume control, minimal active-window lookup, and local-only screenshots
- Typed tool lifecycle events plus executing/action-result UI states
- Five-tool-call cap per user turn and exception isolation
- Smart folder resolver with bounded trusted-root indexing
- Built-in and user-configured folder aliases
- Deterministic fuzzy matching, ambiguity results, and recent-resolution preference
- Canonical explicit-path containment and traversal rejection
- Cached Start Menu application discovery and fuzzy application matching
- Validated local alias configuration

## Run

```powershell
npm install
npm run python:setup
Copy-Item .env.example .env
# Add GEMINI_API_KEY to .env for Live voice and function calling.
npm run dev
```

If PowerShell blocks `npm.ps1`, use `npm.cmd`.

## Not Yet Implemented

- Token-efficient local routing or a Gemini Flash planner
- Developer agent or arbitrary terminal commands
- Screen vision, mouse, or keyboard control
- Long-term memory
- Production tray, installer, or packaged Python runtime

## Next Phase

Phase 5 — Token-Efficient AI Router.
