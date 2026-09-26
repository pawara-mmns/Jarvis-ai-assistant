# UI Architecture

Phase 1 implements the primary desktop-first JARVIS interface. The renderer remains an unprivileged presentation layer and receives real backend health through the existing preload API.

## Component Structure

- `AppShell` owns the top bar, content region, bottom status, and optional development tools.
- `VoiceOrb` is the visual focal point and accepts `state`, optional `intensity`, and main/mini sizing.
- `Waveform` accepts an assistant `mode` and optional normalized `levels`. It uses deterministic simulated levels when none are supplied.
- `AssistantStatus` is driven by the shared state configuration rather than local labels.
- `TranscriptPanel` shows only the current user request, assistant response, execution note, and error.
- `ConnectionStatus` and `BottomStatus` display the real Phase 0 desktop/agent health.
- `MiniAssistant` reuses `VoiceOrb` as a compact visual preview; it is not a second window.
- `DevStateSimulator` appears only when `import.meta.env.DEV` is true.

`assistant-state.config.ts` is the UI source of truth for labels, descriptions, activity labels, tone, orb intensity, and waveform energy. It covers the shared `AssistantState` values:

```text
sleeping
idle
listening
thinking
executing
speaking
confirmation
error
```

## Motion

The orb uses a small fixed set of CSS layers: ambient glow, two rings, shell, core, scan, and state mark. State differences use restrained color, opacity, rotation, scale, and scan behavior. The waveform uses 24 transform-animated bars with deterministic timing; it does not generate random values during rendering.

Continuous motion stops under `prefers-reduced-motion: reduce`. Static color, shape, text, and activity labels keep every state recognizable without animation.

## Future Audio Interface

Phase 2 can supply live normalized values without replacing either visual component:

```tsx
<VoiceOrb state="listening" intensity={audioLevel} />
<Waveform mode="listening" levels={audioLevels} />
```

Phase 1 does not request microphone access or use the Web Audio API.

## Development Simulator

The development footer switches all eight states immediately and applies editable mock transcript, assistant, execution, and error content. Production builds omit this control. It is visual test infrastructure only and contains no command parsing or AI logic.
