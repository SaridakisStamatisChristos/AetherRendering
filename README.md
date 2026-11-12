# Aether Video Engine v1.0

This is a local, reusable **working FFmpeg + Pillow video renderer** and a production-grade prompt for extending it with HyperFrames, Three.js and Kokoro.

## What is verified in this archive

The `src/render.py` pipeline creates real MP4 files from scene records, using eSpeak narration (demo only) or external WAV narration. It produces separately laid-out 9:16 and 16:9 compositions, SRT captions, PNG thumbnail, H.264/AAC outputs and a JSON verification report. Full-frame video and audio decoding is tested using FFmpeg; see generated `output/delivery_report.json`.

The included example is a **technical rendering proof**, not a polished commercial reel. It has scene changes and fades, but not the full word-by-word kinetic-caption system envisioned in `MASTER_PROMPT.md`. It doesn't analyze reference reels, automate music sourcing, or create a Kokoro voice unless those are added. HyperFrames was researched and documented but **could not be installed and tested in this environment**, so the actual sample was rendered with the FFmpeg fallback.

## Install (Ubuntu)

```bash
sudo apt update
sudo apt install -y ffmpeg espeak python3 python3-venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

For production-quality AI narration, set up Kokoro separately (see `src/kokoro_voice.py`), preferably in a Python 3.11/3.12 environment with sufficient model download access. For the HyperFrames route, install Node.js 22+ and run its upstream CLI from a separate project, using `MASTER_PROMPT.md`.

## Render now

```bash
python src/render.py --project project.json --out-dir output --format both --fps 30
```

Render one format:

```bash
python src/render.py --format vertical
python src/render.py --format horizontal
```

Render lower-resolution development outputs:

```bash
python src/render.py --preview --fps 24
```

Render with professional externally synthesized audio from `000.wav`, `001.wav`, ... one per scene:

```bash
python src/render.py --voice-dir voice_wavs --format both --fps 30
```

Silent rendering:

```bash
python src/render.py --silent --format both
```

Each voice file can have arbitrary duration; the renderer probes actual WAV duration and sets scene duration. A short pause is inserted after each scene. The SRT segment timings follow the real duration. For word-by-word timing, extend with an alignment engine (not present).

## Edit your video

Open `project.json` and edit scene title, subtitle, narration, and visual type. The included visual types are `script`, `storyboard`, `frames`, `wave`, `captions`, `aspect`, `export`, `checks`, `proof`. You can extend `scene_image()` for brand-specific illustrations and change the color `accent`. The script derives total duration from scene audio.

## Output

- `output/instagram_1080x1920.mp4` — 1080×1920 (preview files receive a `preview_` prefix)
- `output/youtube_1920x1080.mp4` — 1920×1080 (preview files receive a `preview_` prefix)
- `output/captions.srt` — sentence-per-scene timed subtitles (separate sidecar)
- `output/thumbnail.png` — final vertical scene
- `output/voiceover.wav` — stitched narrated audio
- `output/delivery_report.json` — independently probed streams + full-decode checks

The renderer currently embeds **no burned-in subtitles**; visual scene text is composited into the frames, and SRT is a separate file. It uses very short fades but does not implement the entire advanced motion-design specification. Always check final output by eye and ear.

## Quality gates and known limitations

Automated: dimensions, video codec, audio codec, rough duration, MP4 container, full decode. Not automated: speaker naturalness, transcript correctness, visual appeal, legal asset review, Instagram UI coverage, and human approval. The fallback uses FFmpeg static scenes with fades, **not** fully animated HyperFrames compositions. eSpeak narration is intentionally a synthetic test signal; substitute Kokoro or recordings before publishing.

The script does not generate or include downloadable font files; it uses installed system fonts. No third-party stock footage or copyrighted music is bundled.

## HyperFrames primary renderer (not executed here)

Official docs: https://github.com/heygen-com/hyperframes

```bash
npx hyperframes init my-video
cd my-video
npx hyperframes preview
npx hyperframes lint
npx hyperframes check
npx hyperframes render -o output.mp4
```

For separate aspect ratios, author two compositions and render each with `--composition`; refer to the upstream documentation for the version installed. **Do not claim HyperFrames success unless the CLI actually generates and validates the files.**