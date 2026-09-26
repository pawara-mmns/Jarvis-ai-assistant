# Gemini Live Voice

## Configuration

The Python agent uses the official `google-genai` async Live API with:

- model: `gemini-3.8-live`
- response modality: `AUDIO`
- input and output audio transcription enabled
- no `thinking_level`
- one concise system instruction for short Sinhala, English, and mixed-language replies
- no tools, function declarations, screenshots, second model, or planner

`GEMINI_API_KEY` belongs only in the backend `.env`. `.env.example` contains a blank placeholder. A missing key returns `AI Not Configured` / `Set GEMINI_API_KEY in .env` without stopping health or microphone features.

## Session Lifecycle

The user must enable the microphone and select **Connect AI**. Local WebSocket connection and Gemini connection states are kept separate: disconnected, connecting, ready, active, closing, and error. Duplicate connect calls reuse the in-progress/active session.

An unexpected Gemini connection loss retries at 0.5, 1.5, and 3 seconds, then exposes a safe error for manual retry. Authentication failures do not retry. Disconnect ends current context and closes the remote session. No session is opened on application startup.

Gemini events are translated into the small local protocol. Input/output transcript deltas are merged into the current interaction only. `turn.complete` is remembered until queued output audio finishes, so the UI never reports idle while speech remains audible. Gemini interruption events and local barge-in clear the queue.

The SDK's `session.receive()` iterator covers one model turn. The backend receiver therefore invokes it inside an outer loop while the conversation remains active. `turn.complete` returns the session to ready; only explicit disconnect, shutdown, or a genuine connection failure exits the `client.aio.live.connect()` context.

## Manual Verification

After placing a real key in `.env`, run `npm.cmd run dev`, enable the microphone, and connect AI. Verify:

1. English: “Hello Jarvis, can you hear me?”
2. Sinhala: “ජාවිස්, ඔයාට මාව ඇහෙනවද?”
3. Mixed: “Jarvis, JavaScript object එකක් කියන්නේ මොකක්ද?”
4. Both transcript rows update and native audio is audible.
5. Speaking orb/waveform respond to output, then return to idle after playback.
6. Speaking over JARVIS stops queued output and starts a new turn.
7. Disconnect, continue talking, and confirm the debug readout remains `INPUT LOCAL` with no Gemini session.

Automated tests mock/translate SDK events and never make a paid Gemini call.
