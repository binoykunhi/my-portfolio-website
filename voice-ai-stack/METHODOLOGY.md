# Methodology: Voice AI Latency Benchmarking

This document outlines the experimental setup, pipeline definitions, and metric definitions used in the Voice AI Playground.

## Pipelines

### 1. Batch Pipeline
The batch pipeline follows a traditional sequential processing model:
`Mic Capture -> VAD Silence -> Full Audio Upload -> STT -> LLM -> TTS -> Playback`

- **Capture**: Records audio until 2 seconds of silence is detected.
- **STT**: Uses OpenAI Whisper (Batch API) to transcribe the full audio file.
- **LLM**: Uses OpenAI GPT-4o (Batch API) to generate a full response.
- **TTS**: Uses ElevenLabs (Batch API) to synthesize the full audio response.
- **Playback**: Plays the audio after synthesis is complete.

### 2. Streaming Pipeline
The streaming pipeline optimizes for perceived latency by overlapping processing steps:
`Mic Capture (Stream) -> STT (Stream) -> LLM (Stream) -> TTS (Stream) -> Playback (Stream)`

- **Capture**: Streams audio chunks to STT.
- **STT**: Simulates streaming transcription (or uses real-time API) to provide intermediate results. Final transcript is locked upon VAD silence.
- **LLM**: Streams tokens from GPT-4o as soon as the final transcript is available.
- **TTS**: Consumes LLM tokens and streams audio chunks from ElevenLabs (PCM 16kHz).
- **Playback**: Plays audio chunks immediately as they arrive.

## Latency Metrics

All timings are measured using a **monotonic high-resolution clock** (`time.perf_counter()`) on the client side.

### Definitions

#### Phases
- **User Speech**: Time from first detected voice activity to last detected voice activity.
- **VAD Silence**: The configurable silence duration (default 2s) required to trigger end-of-turn.

#### Latencies
- **Perceived Latency**: Time from the *end of user speech* to the *start of system audio playback*. This is the most critical user-centric metric.
  - Formula: `t_playback_start - t_end_voice_detected`
- **End-to-End (E2E) Latency**: Time from the *start of user speech* to the *start of system audio playback*.
  - Formula: `t_playback_start - t_start_speech_capture`

#### Component Durations
- **STT Duration**: Time from request start to full transcript availability.
- **LLM Duration**: Time from request start to full response availability.
- **LLM Time to First Token** (Streaming only): Time from request start to first token arrival.
- **TTS Time to First Audio** (Streaming only): Time from request start to first audio chunk arrival.

## Reproducibility
- **Hardware**: Uses `sounddevice` for cross-platform audio I/O.
- **Environment**: Python 3.12+ with pinned dependencies.
- **Logging**: All raw timestamps and derived metrics are logged to `results.jsonl` for auditability.
