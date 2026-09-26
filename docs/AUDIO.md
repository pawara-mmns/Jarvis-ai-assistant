# Audio Pipeline

## Local Capture

`AudioEngine` owns one audio-only `getUserMedia` stream. Its `AnalyserNode` continues to provide the Phase 2 30 Hz RMS, 24-bar waveform, and energy VAD summaries. A silent `AudioWorkletNode` branch copies continuous 128-frame mono Float32 blocks without using deprecated `ScriptProcessorNode`; it falls back to analyser frames only when AudioWorklet initialization is unavailable.

## Gemini Input

The Live controller transmits nothing unless the user explicitly connects AI. A stateful linear resampler preserves phase across frames, clamps samples to `-1..1`, and encodes signed little-endian PCM16 at 16 kHz. The chunker emits approximately 40 ms blocks (`audio/pcm;rate=16000`).

Local VAD keeps six chunks (about 240 ms) of rolling pre-roll. Speech start flushes pre-roll and streams current chunks; speech end flushes the partial chunk and sends `audio.end`. When AI is disconnected, microphone capture remains local and Gemini receives zero audio.

## Gemini Output

`AudioPlaybackEngine` decodes base64 PCM16 messages, honors the sample rate in the MIME type (Gemini normally returns 24 kHz), schedules Web Audio buffers in arrival order, and reports real chunk RMS/waveform values. Speaking visuals use those real values. The queue returns to idle only after all scheduled sources end.

Barge-in stops all queued output before new user speech is streamed. A server interruption event performs the same flush. Disable, device switch, disconnect, unload, or disposal stops tracks/nodes, resets conversion state, and closes audio contexts.

No input or output audio is written to disk or analytics.
