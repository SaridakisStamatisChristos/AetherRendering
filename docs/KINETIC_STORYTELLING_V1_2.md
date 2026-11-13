# AetherRendering v1.2 — Kinetic storyboard upgrade

Status: **experimental development branch**, not yet merged into main.

## New capability

The user-approved v1.1 scene animations now get **three timed story beats per scene**, bringing the 30-second sky-blue film to **15 independent micro-reveals**. Each beat is a legible glass-style editorial callout with a seekable entrance, progress line and exit. Animated illustrations also continue moving after their initial entrances, and each new scene gets a short fade at its boundaries.

This does not pretend that adding more 60 fps frames creates more *meaningful animation*. The key improvement is more objects and text changing across those frames.

## Backward-compatible JSON

Every scene can optionally include:

```json
"beats": [
  "Sunlight carries every color",
  "A prism reveals the spectrum",
  "White light becomes a rainbow"
]
```

Constraints: 2–4 beats, maximum 66 characters per beat, no control characters, no JavaScript, no direct HTML. Labels are HTML-escaped and validated before any files or processes are started.

Without beats, an old v1.1 scene compiles as before. Scene times are derived from measured Kokoro WAV durations; beat timing is **scene-relative**, not Whisper word-aligned.

## Render the comparative demo

```bash
npm ci
python -m pip install -r requirements-tts.txt
export HYPERFRAMES_PYTHON="$(command -v python)"
python src/hyperframes_pipeline.py \
  --plan examples/sky_blue_kinetic_30s.json \
  --out-dir build/kinetic/hyperframes \
  --voice af_heart --tts --render --fps 60 \
  --output build/kinetic/exports
```

A dedicated GitHub Actions workflow must pass the full 30-second narration, 1080×1920 and 1920×1080 render, 60 fps verification, audio audibility, and full MP4 decode gates before demo files are preserved in samples/sky-blue-kinetic/.

## Still outside scope

No full 3D character rigs, scene-specific generated images, genuine word timing, audio-driven mouth animation or advanced cinematic footage. These are future integrations with AetherMotion and AetherPaper, not claims for this branch.

## Executed verification — 13 November 2026

The full GitHub Actions pipeline [passed](https://github.com/SaridakisStamatisChristos/AetherRendering/actions/runs/43416014661). The run executed **36 passing Python regression tests**, generated genuine local Kokoro narration, rendered both formats at **60 fps**, verified actual video frame rates and audio, and preserved real MP4s on the feature branch.

| Output | Duration | Resolution | Frame rate | Mean AAC narration level | File size |
|---|---:|---|---:|---:|---:|
| [Portrait MP4](https://raw.githubusercontent.com/SaridakisStamatisChristos/AetherRendering/feature/kinetic-storytelling-v1.2/samples/sky-blue-kinetic/portrait-60fps.mp4) | 29.83 s | 1080×1920 | 60 fps | −22.7 dB | 9.1 MB |
| [Landscape MP4](https://raw.githubusercontent.com/SaridakisStamatisChristos/AetherRendering/feature/kinetic-storytelling-v1.2/samples/sky-blue-kinetic/landscape-60fps.mp4) | 29.83 s | 1920×1080 | 60 fps | −22.7 dB | 8.7 MB |

All files passed FFmpeg full decoding. The saved [verification report](../samples/sky-blue-kinetic/verification.json) is reproducible evidence of technical correctness. This does not yet certify artistic quality, natural language synchronization or readiness to merge.
