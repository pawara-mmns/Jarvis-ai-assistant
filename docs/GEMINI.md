# Gemini Live Voice and Tools

## Configuration

The Python agent uses `google-genai` with `gemini-3.8-live`, AUDIO responses, input/output transcription, and a concise multilingual instruction. The seven approved function declarations use the current SDK's explicit `Behavior.BLOCKING`; no thinking-level override, built-in search, code execution, computer-use tool, second model, or planner is enabled.

`GEMINI_API_KEY` remains backend-only. `JARVIS_SEARCH_URL_TEMPLATE` configures the local browser-search URL and must contain one `{query}` placeholder.

## Session and Function Flow

The user explicitly enables the microphone and connects AI. The backend keeps the same Live connection open across turns and repeatedly consumes the SDK's per-turn `receive()` iterator.

When `response.tool_call` arrives, calls run sequentially through `ToolRegistry`. The backend validates arguments, enforces permission and the five-call turn cap, executes the Windows action, then sends `types.FunctionResponse` with the original function-call ID and compact `ToolResult`. Gemini receives the actual success/failure before it speaks. A failed tool is isolated and does not close the Live session.

The system instruction requires result-grounded confirmations, brief failure explanations, and no invented or premature success. Screenshots are never attached to Gemini; only their friendly filename is returned.

## Lifecycle

Unexpected connection loss retries at 0.5, 1.5, and 3 seconds. Authentication failures do not retry. Disconnect, renderer unload, Electron quit, WebSocket loss, or backend shutdown closes the session. Barge-in still stops queued output and starts a new voice turn.

Automated tests use fake SDK sessions and make no paid API calls. Manual acceptance should verify voice plus all actions listed in [TOOLS.md](TOOLS.md).
