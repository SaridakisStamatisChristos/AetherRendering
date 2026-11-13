# AetherRendering v1.0 production-readiness record

Branch: feature/production-stabilization-v1
Baseline main: b76d390bfd985bf5bef302ac20e1bbc7022a95bf

## Verified

- Existing JSON storyboard validator, Gemini model router logic, five deterministic motion presets, HTML/GSAP compiler and legacy FFmpeg demo retained.
- Historical real Kokoro / HyperFrames MP4s preserved at output/hyperframes_v2/ (historical report confirms two 9.17s decoded MP4s).
- New exact HyperFrames 0.9.37 and GSAP 3.14.2 dependency versions and package-lock.json, installed using npm ci.
- Local GSAP loaded from copied node_modules bundle, not from a CDN.
- New MP4 gate rejects missing audio, invalid codecs, silent/very-low-volume audio (< -58 dB mean), wrong video dimensions or codecs and failed full video decode.
- Real GitHub Actions on feature branch: https://github.com/SaridakisStamatisChristos/AetherRendering/actions/runs/43407993112 — 3 real Kokoro speech segments were generated and both portrait/landscape HyperFrames MP4 exports passed full decoding and measured non-silent audio verification.
- Python tests cover the new audio gates and local-GSAP asset contract. CI artifacts contain the resolved plan and MP4 reports.

## Resolved blocker

A real first run failed because HyperFrames 0.9.37's Kokoro TTS CLI **requires** a Python environment with kokoro-onnx and soundfile. The workflow now installs those required backend packages. This is NOT a second app-defined TTS implementation. Reference failed test: https://github.com/SaridakisStamatisChristos/AetherRendering/actions/runs/43407785254

## Explicitly not yet proved

- Real Gemini generation using the owner's API key (mocked router tests do not prove live account access).
- A completely disconnected render after all model/browser/cache downloads; HyperFrames config still references an external registry.
- Word-level subtitle synchronization, rich illustration/character animation, music/SFX library, permanent GitHub Releases and direct social uploads.
- Artistic editorial approval and full-length 15/30/60s production load tests.

These are separate post-v1.0 improvements or remaining deployment gates; do not claim them complete.

## Installation

Follow docs/LOCAL_SETUP.md. Use Python 3.11+, Node 22+, FFmpeg, npm ci and python -m pip install kokoro-onnx soundfile in the selected environment. Set HYPERFRAMES_PYTHON explicitly if it does not discover that Python.
