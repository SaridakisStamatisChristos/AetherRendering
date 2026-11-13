# Local Installation & Setup — AetherRendering

**Purpose:** Install and run the **current AetherRendering source repository** on your own Ubuntu computer. This is the local counterpart to [the GitHub Actions workflow](../.github/workflows/ai-reel.yml). It covers the deterministic demo, optional Gemini AI Director, local HyperFrames rendering, local Kokoro narration, preview, testing, and troubleshooting.

> **Quick decision:** You do **not** need to fork HyperFrames or Kokoro. Clone **AetherRendering**, install Node.js, Python, FFmpeg, and run the included scripts. The production path invokes Kokoro through the **HyperFrames CLI**, not through a separately cloned Kokoro repository.

## Contents

1. [Requirements](#1-requirements)
2. [Install Ubuntu dependencies](#2-install-ubuntu-dependencies)
3. [Install Node.js 22+](#3-install-nodejs-22)
4. [Clone and prepare Python](#4-clone-and-prepare-python)
5. [Test HyperFrames and Kokoro](#5-test-hyperframes-and-kokoro)
6. [Generate your first local video (no API key)](#6-generate-your-first-local-video-no-api-key)
7. [Generate an original AI-written video with Gemini](#7-generate-an-original-ai-written-video-with-gemini)
8. [Preview and inspect output](#8-preview-and-inspect-output)
9. [Configuration and updating](#9-configuration-and-updating)
10. [Troubleshooting](#10-troubleshooting)
11. [Privacy, limits and known gaps](#11-privacy-limits-and-known-gaps)

## 1. Requirements

- **Recommended OS:** Ubuntu 24.04 LTS, 64-bit. Ubuntu 22.04 also works if you supply **Python 3.11+** separately (its default may be 3.10).
- **Python:** 3.11 or newer; **Node.js:** 22 or newer; **FFmpeg/ffprobe:** on PATH.
- **Other packages:** Git, `espeak-ng`, `libsndfile1`, `ca-certificates`, `curl`.
- Internet connection for the initial npm/browser/voice-model downloads, and for any Gemini requests.
- Free storage for Chromium, cached speech model(s), intermediate frames, and MP4 outputs.
- **GPU is optional.** The workflow can render with CPU/software rendering; longer and more complicated scenes are slower. Don't assume a particular render time.

The main local pipeline is:
`src/ai_director.py` → validated plan → local pinned HyperFrames + GSAP compositions → Kokoro WAV audio → two verified portrait/landscape MP4s.

**No Gemini API key is needed to test the demo or the render engine.** For original AI-written scripts, you will need one.

## 2. Install Ubuntu dependencies

Open **Terminal**. Use an ordinary user account (not root).

```bash
sudo apt update
sudo apt install -y \
  git curl ca-certificates ffmpeg espeak-ng libsndfile1 \
  python3 python3-venv python3-pip

git --version
python3 --version
ffmpeg -version | head -n 1
ffprobe -version | head -n 1
```

If `python3 --version` is **3.11 or newer**, you can use the normal `python3 -m venv` commands in step 4. If it is **3.10 or older**, use the alternative **uv-managed Python** procedure in step 4 instead. Do not replace Ubuntu's system Python.

## 3. Install Node.js 22+

Use a Node version manager (`nvm`) so the system's older `nodejs` package does not interfere. These commands use a versioned [nvm release](https://github.com/nvm-sh/nvm) rather than downloading HyperFrames source.

```bash
# Fetch the nvm installer, inspect it if desired, then execute it
curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.41.0/install.sh -o /tmp/aether-install-nvm.sh
bash /tmp/aether-install-nvm.sh

# Activate nvm in this terminal (or close/reopen Terminal)
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

nvm install 22
nvm alias default 22
node --version
npm --version
npx --version
```

The first number of `node --version` must be **at least 22**. If you already have Node.js 22+, skip this step.

> On future terminal sessions, nvm normally loads via your shell profile. If `npx` cannot be found, open a new terminal or source `$HOME/.nvm/nvm.sh` again.

## 4. Clone and prepare Python

```bash
git clone https://github.com/SaridakisStamatisChristos/AetherRendering.git
cd AetherRendering

# The following uses your Ubuntu Python 3.11+
python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
# HyperFrames TTS requires this local Python backend:
python -m pip install kokoro-onnx soundfile
export HYPERFRAMES_PYTHON="$(command -v python)"
npm ci
python --version

# Run offline tests before attempting rendering
python -m unittest discover -s tests -v
```

**If Ubuntu's Python is older than 3.11:** Instead of the `python3 -m venv .venv` command above, create the environment with an independent interpreter managed by [uv](https://docs.astral.sh/uv/getting-started/installation/). Run these commands **from the cloned repository**:

```bash
curl -LsSf https://astral.sh/uv/install.sh -o /tmp/aether-install-uv.sh
sh /tmp/aether-install-uv.sh
export PATH="$HOME/.local/bin:$PATH"

uv python install 3.12
uv venv --python 3.12 .venv
source .venv/bin/activate

python -m pip --version || python -m ensurepip --upgrade
python -m pip install -r requirements.txt
python -m pip install kokoro-onnx soundfile
export HYPERFRAMES_PYTHON="$(command -v python)"
npm ci
python -m unittest discover -s tests -v
```

You do **not** need to run both Python-environment methods. Use one.

The **HyperFrames CLI requires `pip install kokoro-onnx soundfile`** in the Python environment used by HyperFrames. The CLI remains the one speech interface; this is its internal ONNX backend, not an additional bespoke TTS engine. The optional `src/kokoro_voice.py` file is a *separate* Python adapter and not part of the main commands in this guide.

## 5. Test HyperFrames and Kokoro

Always run these commands from **AetherRendering's repository root**, with the Python virtual environment activated.

```bash
# Validate the external video engine and prepare Chromium
node_modules/.bin/hyperframes info
node_modules/.bin/hyperframes doctor
node_modules/.bin/hyperframes browser ensure

# Show available voices
node_modules/.bin/hyperframes tts --list

# Synthesize a small audio test
mkdir -p build/smoke
node_modules/.bin/hyperframes tts "Welcome to Aether Rendering." \
  --voice af_heart \
  --output build/smoke/narration.wav

# Confirm the WAV file was created and can be decoded
ls -lh build/smoke/narration.wav
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1 build/smoke/narration.wav
```

The first speech generation may download voice-model data. The TTS feature operates locally once installed and does **not** need a Gemini key. `node_modules/.bin/hyperframes` uses the upstream package published to npm.

If `doctor` reports missing browser dependencies, follow its output, rerun `browser ensure`, and test again.

## 6. Generate your first local video (no API key)

This is the **recommended first full end-to-end render**.

```bash
# From AetherRendering/ with .venv active:
python src/ai_director.py \
  --provider demo \
  --topic "How an AI video engine works" \
  --duration 15 \
  --out build/video_plan.json

python src/hyperframes_pipeline.py \
  --plan build/video_plan.json \
  --out-dir build/hyperframes \
  --voice af_heart \
  --tts \
  --render \
  --output build/exports \
  --fps 30
```

The pipeline produces:

| File | Meaning |
|---|---|
| `build/video_plan.json` | Source scene plan |
| `build/hyperframes/resolved_plan.json` | Scene timing after generating speech |
| `build/hyperframes/vertical/index.html` | Portrait HTML/GSAP animation |
| `build/hyperframes/horizontal/index.html` | Landscape HTML/GSAP animation |
| `build/exports/vertical.mp4` | 1080 × 1920 (Instagram/Reels) |
| `build/exports/horizontal.mp4` | 1920 × 1080 (landscape YouTube) |
| `build/exports/report.json` | Probe and full-decode verification |

**The duration is approximate.** Measured Kokoro speech duration determines the final timeline. The `demo` provider uses generic fixed text, not an AI-generated documentary script.

To play the output on Ubuntu, open `build/exports/vertical.mp4` in your video player. You can also use `xdg-open build/exports/vertical.mp4` if a default player is configured.

### Verify the MP4 independently

```bash
ffprobe -v error -show_entries stream=codec_name,codec_type,width,height \
  -show_entries format=duration -of json build/exports/vertical.mp4

ffmpeg -v error -xerror -i build/exports/vertical.mp4 -f null -
```

If the decode command exits without errors, the file can be decoded; this does not by itself prove artistic quality or perfect synchronization.

## 7. Generate an original AI-written video with Gemini

A local **Gemini API key** is required for `provider=gemini`. Keep it out of command history and files that could be committed.

```bash
# Read the key without echoing its contents; do this in the same terminal
read -r -s -p "Gemini API key: " GEMINI_API_KEY
echo
export GEMINI_API_KEY
```

Check models available to your project:

```bash
python src/ai_director.py --topic "unused" --list-models
```

For automatic routing, open `config/gemini_router.json` and make sure the **model IDs actually returned by discovery** are listed and enabled. The initial configuration contains candidate model IDs; it does not guarantee that Google exposes them. Populate realistic per-model caps based on your own [Google AI Studio quota dashboard](https://aistudio.google.com/).

Then:

```bash
python src/ai_director.py \
  --provider gemini \
  --topic "How stars become black holes" \
  --duration 30 \
  --model auto \
  --complexity auto \
  --out build/video_plan.json

python src/hyperframes_pipeline.py \
  --plan build/video_plan.json \
  --out-dir build/hyperframes \
  --voice af_heart \
  --tts \
  --render \
  --output build/exports \
  --fps 30

unset GEMINI_API_KEY
```

`model=auto` selects an eligible configured model using the router and can fall back after eligible temporary errors. If no discovered model matches, **the call stops**; update your config rather than assuming the key unlocks every model. The repository's local usage ledger counts this application's requests only, not usage from other applications sharing your Google project.

For more details, see [Gemini router guide](GEMINI_ROUTER.md).

## 8. Preview and inspect output

To inspect the generated animation **without** downloading speech models or producing an MP4, compile an existing plan:

```bash
python src/ai_director.py \
  --provider demo --topic "Previewing animation" --duration 15 \
  --out build/video_plan.json

python src/hyperframes_pipeline.py \
  --plan build/video_plan.json --out-dir build/hyperframes

HYPERFRAMES_BIN="$(realpath node_modules/.bin/hyperframes)"
cd build/hyperframes/vertical
"$HYPERFRAMES_BIN" lint
"$HYPERFRAMES_BIN" preview
```

The HyperFrames preview server usually opens at `http://localhost:3002`. Use Ctrl+C to stop a foreground preview, then return to the repo root:

```bash
cd ../../..
```

**Caution:** `preview` shows the visual composition, but a full narrated export requires `--tts --render`. The current renderer generates portrait and landscape layouts separately; it does not merely stretch a portrait image to landscape.

## 9. Configuration and updating

| Task | Where |
|---|---|
| Change video topic and target duration | `src/ai_director.py` command flags |
| Choose a voice | `src/hyperframes_pipeline.py --voice ...` (run `hyperframes tts --list`) |
| Select Gemini model and routing tier | `--model auto`, `--complexity auto` or explicit values |
| Configure candidate model IDs and protective caps | `config/gemini_router.json` |
| Change motion templates and design | `src/hyperframes_pipeline.py` |
| Use legacy FFmpeg/Pillow demonstration | `python src/render.py --project project.json --out-dir output --format both --fps 30` |
| Check latest repository changes | `git pull --ff-only` |

For future sessions:

```bash
cd ~/AetherRendering
source .venv/bin/activate
# If needed: source "$HOME/.nvm/nvm.sh"
python -m unittest discover -s tests -v
```

The `~/AetherRendering` path assumes you cloned from your home directory; adjust if you chose a different location.

**Dependency pinning:** `package.json` pins HyperFrames 0.9.37 and GSAP 3.14.2. `package-lock.json` freezes all transitive npm dependencies. Use `npm ci` rather than unpinned `npx` invocation; still record/cache the browser and Kokoro model files.

**Don't commit secrets or generated output inadvertently.** Before `git add`/`git commit`, inspect `git status`. Keep your own `build/`, speech WAVs, local usage state and secrets private as appropriate.

## 10. Troubleshooting

| Symptom | What to do |
|---|---|
| `node` or `npx` not found | Reload nvm and confirm Node ≥22 with `node --version`. |
| Python virtual environment fails | Use Python ≥3.11 or the uv-managed Python 3.12 alternative above. |
| `hyperframes browser ensure` fails | Check network, filesystem permissions, disk space, and `npx hyperframes doctor`. |
| TTS returns no WAV | Run `npx hyperframes tts --list`; verify voice ID, cached model download, and error logs. |
| Output has no audio | Re-run with **both** `--tts` and `--render`; confirm the `kokoro-onnx soundfile` Python backend and `HYPERFRAMES_PYTHON`, inspect generated WAVs and `audio_verified` in report.json. |
| Gemini says no configured model found | Compare `--list-models` output with `config/gemini_router.json`; enable a real, accessible model. |
| Gemini HTTP 429 | Reduce requests or wait for quota reset; configured fallback cannot bypass project-wide limits. |
| Missing `build/exports/*.mp4` | Check the command's error output. The pipeline aborts on lint/render/verification failures. |
| Video duration differs from requested seconds | Speech WAV lengths determine scene durations; target duration is approximate. |
| Video appears simplistic | Current templates use animated headings/abstract ornamentation only; images, stock footage and 3D are future work. |
| Video works on GitHub but not locally | Compare Node, Python and `npx hyperframes info` output with the workflow logs. |
| GitHub provides ZIP, not MP4 | That's an Actions artifact. Extract it and find `build/exports/vertical.mp4` and `horizontal.mp4`. |

The built-in repository smoke test can still be used via [GitHub Actions](https://github.com/SaridakisStamatisChristos/AetherRendering/actions/workflows/ai-render-smoke.yml).

## 11. Privacy, limits and known gaps

- **Local rendering ≠ offline AI:** When `--provider gemini` is selected, the script and topic go to Google's Gemini API. Demo script generation, Kokoro speech and HyperFrames rendering run locally after their dependencies are downloaded.
- The current development branch copies **GSAP from locally installed, pinned npm dependencies** into each composition, rather than loading it from a CDN. A fully disconnected render still requires independent verification of cached browser, voice model and HyperFrames resources.
- The current system does **not** automatically generate video footage, cinematic 3D objects, music, licensed sound effects, Greek-language TTS, word-aligned captions, or social-platform uploads.
- FFmpeg's success checks are technical, not an artistic or factual editorial review.
- Model quota controls are safeguards, not official project quota introspection or a monetary spending limit.
- If you publish a video, check factual claims, licenses, subtitles, loudness and accessibility by actually watching and listening to the export.

### Upstream references

- [HyperFrames CLI documentation](https://github.com/heygen-com/hyperframes/blob/main/packages/cli/README.md)
- [HyperFrames detailed CLI guide](https://github.com/heygen-com/hyperframes/blob/main/docs/packages/cli.mdx)
- [Official Kokoro](https://github.com/hexgrad/kokoro)
- [Kokoro-ONNX (optional alternative)](https://github.com/thewh1teagle/kokoro-onnx)
- [Gemini API models](https://ai.google.dev/gemini-api/docs/models)
- [Gemini API rate limits](https://ai.google.dev/gemini-api/docs/rate-limits)

---

**Minimal reminder:** install the dependencies, clone this repository, activate `.venv`, run the demo AI Director command, and run the HyperFrames pipeline with `--tts --render`. You will receive actual MP4 files under `build/exports/`.
