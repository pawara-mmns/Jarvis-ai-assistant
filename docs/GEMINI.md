# Future Gemini Architecture

Gemini is not integrated in Phase 0. A later implementation will follow this routing model:

```text
Local deterministic actions → no Gemini
Voice AI                   → Gemini Live
Complex reasoning/planning → Gemini Flash
```

Gemini will never directly execute OS code. Models may request a tool from an explicit approved registry; local validation, permissions, confirmation rules, and execution remain authoritative.

## Token Efficiency

- Detect wake words locally.
- Run voice activity detection locally.
- Do not maintain always-on cloud audio streaming.
- Send only relevant context.
- Prefer short responses when they satisfy the request.
- Route work to the smallest suitable model or deterministic local path.
- Track usage so costly paths remain visible and controllable.

No API keys or active Gemini configuration belong in Phase 0.
