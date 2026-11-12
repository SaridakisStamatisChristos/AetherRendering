# AetherRendering

**An AI-assisted video engine: Topic → Gemini storyboard → HyperFrames animation → Kokoro narration → verified MP4.**

AetherRendering produces short, narrated videos in **Instagram/Reels portrait (1080 × 1920)** and **YouTube landscape (1920 × 1080)** formats. It contains an AI Director, a Gemini model router, a deterministic HTML/JavaScript scene compiler, local speech synthesis through HyperFrames' Kokoro integration, and FFmpeg validation. A separate FFmpeg/Pillow demonstration renderer remains available as a fallback.

> **New here?** You do **not** need to fork HyperFrames or Kokoro, install either on your computer, or obtain a Gemini API key to try the *demo*. Start with [**Quick start: GitHub Actions**](#1-quick-start-no-installation). For **original AI-written scripts**, see [Enable Gemini](#2-enable-gemini-ai-generation).

[Run a video workflow](https://github.com/SaridakisStamatisChristos/AetherRendering/actions/workflows/ai-reel.yml) · [Verified sample MP4s](#sample-videos) · [Ubuntu setup](#4-local-ubuntu-installation) · [Gemini router configuration](config/gemini_router.json)

## What is actually implemented?

| Capability | Status |
|---|---|
| Generate a demonstration storyboard without a key | Implemented |
| Generate a topic-specific JSON storyboard using Gemini | Implemented; needs your Gemini API key |
| Discover and select compatible configured Gemini models | Implemented; live access depends on your account |
| Configurable model priorities, protective limits, fallback and usage audit | Implemented |
| Compile storyboard into HTML/CSS/GSAP for both aspect ratios | Implemented |
| Synthesize Kokoro audio through HyperFrames CLI | Implemented; a GitHub demonstration has rendered successfully |
| Render portrait and landscape MP4s, verify codec/dimensions/full decode | Implemented; demonstration outputs preserved |
| Create scene-specific photos, 3D assets, video clips, or music | **Not yet implemented** |
| Word-by-word timed captions in the new engine | **Not yet implemented** |
| Upload each new video directly to Instagram/YouTube | **Not implemented** |
| Automatically create GitHub Releases for each new video | **Not yet implemented** |

The current aesthetic uses **animated typography and simple motion graphics**. Do not confuse it with an autonomous, fully cinematic video-editing system. AI-created content still requires factual and editorial review.

## How the system works

```text
Your topic
   |
   v
AI Director (demo text OR Gemini-generated script and scene plan)
   |
   v
Validated JSON storyboard ── Gemini model router (if enabled)
   |
   v
HyperFrames compiler: HTML + CSS + GSAP for portrait and landscape
   |
   +──> Kokoro narration WAVs (through HyperFrames CLI)
   |               |
   +───────────────+──> Actual speech timing + synchronized audio tracks
                           |
                           v
                     HyperFrames MP4 render
                           |
                           v
                    FFmpeg/ffprobe checks
                           |
                           v
                   vertical.mp4 + horizontal.mp4
```

The AI **does not execute arbitrary model-written JavaScript**. It generates a restricted, validated JSON scene plan, which `src/hyperframes_pipeline.py` compiles into animation code. Available motion presets are `rise`, `slide`, `zoom`, `rotate`, and `pop`.

---

## 1. Quick start (no installation)

This is the simplest way to create a video using GitHub's computers.

1. Open [**Actions → AI Video — HyperFrames + Kokoro**](https://github.com/SaridakisStamatisChristos/AetherRendering/actions/workflows/ai-reel.yml).
2. Select **Run workflow** on the `main` branch.
3. Choose these values for your first test:

   | Workflow input | Recommended first value |
   |---|---|
   | **topic** | `How black holes work` |
   | **provider** | `demo` |
   | **model** | `auto` (ignored in demo mode) |
   | **complexity** | `auto` |
   | **seconds** | `25` |
   | **voice** | `af_heart` |
   | **render_video** | `true` |

4. Click **Run workflow**. Open the new run to see build logs and status.
5. When successful, scroll to **Artifacts** and download `AetherRendering-AI-<run-number>`.

### Why does GitHub give me a ZIP?

**This is expected.** GitHub Actions packages its output files into a ZIP artifact. Extract it to access the MP4 files. The main outputs are:

```text
build/
  video_plan.json
  gemini_router_audit.json   # when Gemini routing is used
  hyperframes/
    vertical/index.html
    horizontal/index.html
    resolved_plan.json
  exports/
    vertical.mp4            # Instagram/Reels portrait
    horizontal.mp4          # YouTube landscape
    report.json             # render verification
```

Selecting `render_video=false` compiles the video project **without** generating the MP4s. On the first full run, browser and speech-model downloads may take additional time. The workflow retains artifacts for **up to 90 days**, not indefinitely.

### Sample videos

You can access the previously committed HyperFrames/Kokoro demonstration MP4s directly, without downloading an Actions artifact ZIP:

- [**Instagram portrait MP4 — HyperFrames + Kokoro**](output/hyperframes_v2/instagram.mp4)
- [**YouTube landscape MP4 — HyperFrames + Kokoro**](output/hyperframes_v2/youtube.mp4)
- [Verification result](output/hyperframes_v2/verification.json)
- [Earlier FFmpeg portrait demonstration](output/instagram_1080x1920.mp4)
- [Earlier FFmpeg landscape demonstration](output/youtube_1920x1080.mp4)

On Android, GitHub may download the MP4 rather than play it inside the browser. Open the downloaded video in Files/Gallery.

---

## 2. Enable Gemini AI generation

**Demo mode needs no Gemini key.** Gemini mode uses Google AI Studio to generate an original script and structured storyboard.

1. Create an API key in [Google AI Studio](https://aistudio.google.com/apikey).
2. Open the repository's [**Settings → Secrets and variables → Actions**](https://github.com/SaridakisStamatisChristos/AetherRendering/settings/secrets/actions).
3. Choose **New repository secret** and set its name to **`GEMINI_API_KEY`**. Paste your key as the secret value.
4. Return to [**AI Video — HyperFrames + Kokoro**](https://github.com/SaridakisStamatisChristos/AetherRendering/actions/workflows/ai-reel.yml) and click **Run workflow**.
5. Example inputs:

   | Input | Value |
   |---|---|
   | `topic` | `What makes a black hole different from a star?` |
   | `provider` | `gemini` |
   | `model` | `auto` |
   | `complexity` | `auto` |
   | `seconds` | `30` |
   | `voice` | `af_heart` |
   | `render_video` | `true` |

6. After the workflow finishes, download and extract its artifact and open `build/exports/vertical.mp4` or `horizontal.mp4`.

**Never paste the API key into the repository, the workflow input fields, this README, or a chat message.** GitHub Actions supplies it privately through the repository secret.

### Which Gemini model will it use?

The project has a **Gemini Model Router**:

- `model=auto`: discover compatible Google text-generation models and try enabled candidates from the configured priorities.
- `complexity=auto`: automatically select a routing tier; alternatively choose `simple`, `standard`, or `complex`.
- `model=<configured-id>`: manually choose a model; manual selection disables model fallback.
- On retryable rate-limit or temporary errors, the router can try a different enabled model. It does **not** rotate after authentication or permission failures.

Configure candidates and your own limits in [`config/gemini_router.json`](config/gemini_router.json). **Model IDs in that file are candidates, not proof of availability.** Your Google account determines which models and quotas are actually usable.

### Set your quotas correctly

A per-model configuration looks like this (numbers **illustrative only**):

```json
{
  "enabled": true,
  "max_requests_per_day": 100,
  "max_requests_per_minute": 5,
  "max_tokens_per_minute": 20000,
  "max_output_tokens": 4096
}
```

Use your actual Google AI Studio project limits, preferably with a safety margin. In the default configuration, `null` means **there is no additional local cap**, not that Google's quota is unlimited. Rate limits are typically shared at the project level; AetherRendering cannot see requests made by other apps using the same Google project.

Gemini request attempts are recorded in `state/gemini_usage.json` and a redacted audit is written to `build/gemini_router_audit.json`. The hosted workflow commits its usage state before rendering. Daily ledger buckets follow the **America/Los_Angeles** calendar. The router is not a billing/spending cap.

See [**Gemini Router documentation**](docs/GEMINI_ROUTER.md) for detailed behavior.

---

## 3. What are HyperFrames and Kokoro?

| Tool | What it does | In this project |
|---|---|---|
| [**HyperFrames**](https://github.com/heygen-com/hyperframes) | Renders browser-based HTML/JavaScript video compositions | Primary renderer, invoked via `npx --yes hyperframes` |
| [**Kokoro**](https://github.com/hexgrad/kokoro) | Text-to-speech model family | Generates WAV narration via the HyperFrames CLI `tts` command |
| [**Kokoro-ONNX**](https://github.com/thewh1teagle/kokoro-onnx) | Alternative local Python/ONNX implementation | Optional dependency / possible independent integration |
| **Gemini** | Creates the storyboard and narration text | Optional AI Director accessed with your API key |
| **FFmpeg/ffprobe** | Checks video/audio streams and verifies decodability | Verification and legacy fallback rendering |

No fork of either upstream project is required. The new pipeline's `prepare_audio()` calls `npx --yes hyperframes tts ...` and measures each WAV with `ffprobe`; scene durations are then derived from the actual speech timings. The optional `src/kokoro_voice.py` is a **different** Python adapter for the older FFmpeg path and uses the `kokoro` package, not the main HyperFrames TTS route.

**Language note:** The currently integrated Kokoro voices do not establish Greek TTS support. A separate compatible Greek-language speech backend would be needed.

---

## 4. Local Ubuntu installation

You can develop locally instead of using GitHub's runner. The basic system does **not** require a dedicated GPU.

### Prerequisites

- Ubuntu Linux and Git
- Python **3.11 or newer** with `venv` and `pip`
- Node.js **22 or newer** with `npm`/`npx` (from [nodejs.org](https://nodejs.org/en/download) if your distro provides an older version)
- FFmpeg, `espeak-ng`, `libsndfile1`
- Internet access for the initial CLI, browser and model downloads

```bash
sudo apt update
sudo apt install -y git ffmpeg espeak-ng libsndfile1 \
  python3 python3-venv python3-pip

# Check prerequisites
python3 --version
node --version
npx --version
ffmpeg -version
```

If `node --version` is below `v22`, install a newer version of Node.js before continuing.

### Clone and set up

```bash
git clone https://github.com/SaridakisStamatisChristos/AetherRendering.git
cd AetherRendering

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Dependencies used in the GitHub integration and optional speech adapters
python -m pip install kokoro-onnx soundfile

# Verify the Python parts
python -m unittest discover -s tests -v

# Prepare the headless browser used for video rendering
npx --yes hyperframes browser ensure
```

The `npx` CLI currently resolves HyperFrames without a committed, pinned npm version. For reproducible production, pin a tested release and record the installed version in your run report.

### Option A: Local demo video (no Gemini key)

Run these commands from the repository root:

```bash
python src/ai_director.py \
  --topic "Why lightning comes before thunder" \
  --provider demo \
  --duration 25 \
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

You should get:

```text
build/exports/vertical.mp4
build/exports/horizontal.mp4
build/exports/report.json
```

### Option B: Local AI-generated video

Enter the API key for the current shell without putting it in the command text:

```bash
read -r -s -p "Gemini API key: " GEMINI_API_KEY
echo
export GEMINI_API_KEY
```

You can see which models the key exposes with:

```bash
python src/ai_director.py --topic "model discovery" --list-models
```

Then create and render a video:

```bash
python src/ai_director.py \
  --topic "What are black holes?" \
  --provider gemini \
  --model auto \
  --complexity auto \
  --duration 30 \
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

**Duration is approximate.** Real narration WAV lengths determine the final timeline. The requested seconds are a creative target, not a guaranteed output duration.

### Option C: Compile video code without rendering

This is useful when developing scene templates or reviewing the storyboard:

```bash
python src/ai_director.py --topic "Motion graphics" --provider demo --duration 25
python src/hyperframes_pipeline.py --plan build/video_plan.json \
  --out-dir build/hyperframes

cd build/hyperframes/vertical
npx --yes hyperframes preview
```

This produces HTML/GSAP composition files and a resolved plan. **No WAV or MP4** is generated without `--tts --render`. Run subsequent Python commands again from the repository root.

---

## 5. Project structure and outputs

```text
AetherRendering/
├── README.md
├── MASTER_PROMPT.md                 # Design goals / production directive
├── project.json                     # Legacy FFmpeg demo configuration
├── config/gemini_router.json        # Models, priorities, protective caps
├── docs/
│   ├── AI_RENDERING.md
│   └── GEMINI_ROUTER.md
├── src/
│   ├── ai_director.py              # Script/JSON plan generation
│   ├── gemini_router.py            # Model discovery, rate guardrails, audit
│   ├── hyperframes_pipeline.py     # HTML + audio + MP4 composition
│   ├── kokoro_voice.py             # Optional older Python voice adapter
│   └── render.py                   # FFmpeg/Pillow fallback
├── tests/
├── reels/demo/                    # Committed demo HTML compositions
├── output/                        # Committed previously verified demos
│   └── hyperframes_v2/
│       ├── instagram.mp4
│       ├── youtube.mp4
│       └── verification.json
└── .github/workflows/
    ├── ai-reel.yml                 # Primary GitHub Actions video workflow
    ├── ai-render-smoke.yml        # HyperFrames/Kokoro smoke test
    ├── router-tests.yml           # Offline routing regression tests
    └── render.yml                 # Legacy FFmpeg renderer
```

Typical **new** outputs (created during a run, not automatically committed to the repository):

| Path | Meaning |
|---|---|
| `build/video_plan.json` | Validated scene storyboard |
| `build/gemini_router_audit.json` | Redacted Gemini model selection audit (Gemini mode) |
| `build/hyperframes/vertical/index.html` | Generated portrait animation source |
| `build/hyperframes/horizontal/index.html` | Generated landscape animation source |
| `build/hyperframes/resolved_plan.json` | Actual speech-adjusted timeline |
| `build/exports/vertical.mp4` | Vertical MP4 |
| `build/exports/horizontal.mp4` | Horizontal MP4 |
| `build/exports/report.json` | FFmpeg/ffprobe validation result |

A new `ai-reel.yml` run currently uploads a **ZIP Actions artifact**, rather than publishing permanent Release assets or committing each MP4 to Git history. Preserve important videos separately.

---

## 6. Customization and scene format

Change the topic, model, duration, complexity and voice using the GitHub Actions inputs or CLI flags. To change motion design, extend the templates in `src/hyperframes_pipeline.py` rather than telling Gemini to invent unsupported visual effects.

The current JSON storyboard contains a topic, an optional `#RRGGBB` accent, and **2–30 scenes**. Each scene has a title, subtitle, narration, numeric duration and supported motion preset. For example:

```json
{
  "topic": "Why the sky is blue",
  "accent": "#4CE0C1",
  "scenes": [
    {
      "title": "BLUE LIGHT",
      "subtitle": "Atmospheric scattering",
      "narration": "Air molecules scatter shorter wavelengths of visible light more strongly.",
      "duration": 5,
      "motion": "rise"
    },
    {
      "title": "THE SKY",
      "subtitle": "Light reaches us from every direction",
      "narration": "Scattered blue light arrives at our eyes from many directions across the sky.",
      "duration": 5,
      "motion": "zoom"
    }
  ]
}
```

The AI Director validates scene fields and timing; an unsupported motion or malformed JSON causes the build to stop before rendering. The generated visuals currently use animated headings, subheadings, decorative shapes and a progress bar—not custom stock footage or complex 3D scenes.

### Legacy FFmpeg rendering

The older project remains available independently:

```bash
python src/render.py --project project.json --out-dir output --format both --fps 30
# Faster low-resolution preview:
python src/render.py --preview --fps 24
```

It uses the `project.json` scenes and eSpeak demonstration narration unless you supply WAVs with `--voice-dir voice_wavs` named `000.wav`, `001.wav`, etc. It is a technical fallback, **not the HyperFrames engine**. Its own `output/captions.srt` is separate from the new pipeline and does not provide word-synchronized captions.

---

## 7. Testing and quality checks

Run the Python tests:

```bash
python -m unittest discover -s tests -v
```

The HyperFrames pipeline runs `ffprobe` for resolution and H.264 codec and attempts a **full FFmpeg decode** for each MP4. You can independently check an output:

```bash
ffprobe -v error -show_entries stream=codec_name,codec_type,width,height \
  -show_entries format=duration -of json build/exports/vertical.mp4
ffmpeg -v error -xerror -i build/exports/vertical.mp4 -f null -
```

Expected video dimensions are **1080×1920 portrait** and **1920×1080 landscape**. These checks establish that a file can be decoded; they do not prove visual beauty, speech naturalness, factual accuracy, synchronized *individual words*, or publication readiness. Always watch the exported video.

### Troubleshooting

| Symptom | Check / action |
|---|---|
| **Only a ZIP appeared** | This is the GitHub Actions artifact. Download, extract, find `build/exports/*.mp4`. |
| **No MP4 is present** | Set `render_video=true`; inspect TTS/HyperFrames steps and logs. |
| **`GEMINI_API_KEY missing`** | Create the correctly named Actions repository secret. |
| **No suitable Gemini model** | Check real model availability, key, quotas, enabled `config/gemini_router.json` candidates. |
| **429 / rate limits** | Lower usage; router may try an allowed fallback, but cannot bypass project limits. |
| **Node is too old / `npx` not found** | Install Node.js 22+ and confirm `node --version`. |
| **Headless browser missing** | Run `npx --yes hyperframes browser ensure`. |
| **Kokoro voice generation fails** | Check chosen voice and initial model download; read the TTS step log. |
| **Video length differs from target** | Timing follows measured narration, not the `seconds` value exactly. |
| **Visuals seem like slides** | Current engine generates typographic motion graphics; media/3D/advanced editing remain future work. |
| **Results change between runs** | The HyperFrames package is currently unpinned; use a tested pinned version for stable builds. |
| **State/ledger push fails** | Check workflow `contents: write`, branch protection and concurrency rules. |
| **Can't watch GitHub MP4 on Android** | Choose the raw/download link; play the downloaded file locally. |

---

## 8. Security, licensing, limitations and next improvements

- Store API credentials only in GitHub **Actions secrets** or a temporary local environment; never commit keys.
- Gemini-generated storyboards are treated as **untrusted structured data**. They are validated, not executed as arbitrary model-authored JavaScript.
- Model quotas and token estimates are protective approximations. The router cannot enforce Google billing limits or see other apps' usage.
- Generated HTML currently loads GSAP from a CDN, and HyperFrames CLI usage is not yet version-pinned. Fully offline and reproducible builds require extra dependency work.
- GitHub Actions consumes compute minutes and artifacts expire; retain finished work outside temporary artifacts.
- Verify rights and licensing before adding stock footage, graphics, music or voices from external sources.
- The system does not yet generate elaborate image/3D assets, mix music, align individual spoken words, automatically perform factual research, or upload to social platforms.

**Suggested roadmap:** pin and record exact upstream versions; add versioned GitHub Releases for individual MP4 downloads; implement richer reusable motion templates and visual assets; add word-timed captions/music/sound effects; support alternative narrators (including Greek); and introduce human creative review gates.

### Reference guides

- [Detailed AI rendering guide](docs/AI_RENDERING.md)
- [Gemini model router guide](docs/GEMINI_ROUTER.md)
- [Production master directive](MASTER_PROMPT.md)
- [HyperFrames source and documentation](https://github.com/heygen-com/hyperframes)
- [Kokoro GitHub](https://github.com/hexgrad/kokoro)
- [Kokoro-ONNX GitHub](https://github.com/thewh1teagle/kokoro-onnx)
- [Google Gemini API models](https://ai.google.dev/gemini-api/docs/models)
- [Google Gemini API rate limits](https://ai.google.dev/gemini-api/docs/rate-limits)

---

**One-sentence quick start:** Add `GEMINI_API_KEY` as an Actions secret, [run **AI Video — HyperFrames + Kokoro**](https://github.com/SaridakisStamatisChristos/AetherRendering/actions/workflows/ai-reel.yml) with `provider=gemini`, `model=auto`, and `render_video=true`, then download the Actions ZIP and open the resulting MP4 files in `build/exports/`.