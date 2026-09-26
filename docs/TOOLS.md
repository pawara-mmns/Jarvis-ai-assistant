# Safe Desktop Tools

## Execution Contract

`ToolRegistry` is the only bridge from Gemini function calls to local actions. It performs exact-name lookup, Pydantic argument validation, permission enforcement, timeout handling, exception isolation, and audit logging. Every action returns a compact `ToolResult` with `success`, a friendly `message`, an optional stable error code, and only the minimal data needed by Gemini.

Permissions are `SAFE`, `CONFIRM`, and `BLOCKED`. All Phase 4 tools are `SAFE`; no `CONFIRM` or destructive tool is exposed. Calls are explicitly blocking, run sequentially, and are capped at five per user turn.

## Available Tools

| Tool | Purpose | Key boundary |
| --- | --- | --- |
| `open_app` | Open an app by alias or friendly installed name | Fixed definitions, configured logical aliases, or trusted Start Menu shortcuts; no executable paths |
| `open_url` | Open an absolute HTTP(S) URL in the default browser | All other schemes rejected |
| `search_web` | Open an encoded query using `JARVIS_SEARCH_URL_TEMPLATE` | No Gemini Search API |
| `open_folder` | Open a folder by friendly name, alias, ambiguity candidate, or approved path | Cached trusted-root index; navigation only |
| `audio_control` | Set 0–100 output volume, mute, or unmute | Default speaker endpoint only |
| `get_active_window` | Return bounded app/title metadata | No content, path, PID, or keystrokes |
| `take_screenshot` | Save a PNG under Pictures/JARVIS/Screenshots | Local file only; image never enters model context |

## Windows Boundary

Windows-specific operations live in `agent/tools/platform/windows.py`. Trusted executables use structured `subprocess.Popen([...], shell=False)`; URLs, folders, and Settings use `ShellExecuteW`; output volume uses pycaw/Core Audio; foreground metadata uses User32/Kernel32; screenshots use Pillow `ImageGrab`.

`open_folder` accepts `query` and an optional `candidate` after ambiguity. The backend still accepts the former `path` field for local backward compatibility, but it is not advertised to Gemini. Successful resolution returns only a friendly name. Ambiguity returns at most four display names.

Resolver settings are `JARVIS_FOLDER_ROOTS`, `JARVIS_FOLDER_INDEX_MAX_DEPTH`, `JARVIS_RESOLVER_REFRESH_SECONDS`, and `JARVIS_USER_ALIASES_PATH`. Copy `config/user-aliases.example.json` to the ignored `config/user-aliases.json` for local aliases.

Gemini receives compact declarations, proposes a call, and gets a `FunctionResponse` with the matching call ID only after registry execution. Technical exceptions stay in local logs. The renderer receives sanitized lifecycle events and never receives raw arguments.

There is no generic shell, PowerShell, CMD, Python, arbitrary-program, mouse, keyboard, screen-analysis, developer, memory, or routing tool in Phase 4.
