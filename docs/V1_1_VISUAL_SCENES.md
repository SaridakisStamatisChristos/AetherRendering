# AetherRendering v1.1 — Reusable visual scenes and narration captions

## Design objective
Add a better visual system to the existing HyperFrames/Kokoro pipeline without breaking v1.0 and without AI-generated executable HTML. Input is still validated JSON.

## Visual presets
Optional per-scene `visual` enum: `abstract` (original style; default), `spectrum`, `scatter`, `atmosphere`, `wavelengths`, `sunset`. All five new treatments are local self-contained vector illustrations with timeline-seekable GSAP reveals. No image API, stock footage, or runtime CDN.

Example: `{"title":"LIGHT MEETS AIR","subtitle":"Molecules scatter sunlight","narration":"...","duration":6,"motion":"slide","visual":"scatter"}`.

## Subtitles
A `captions.srt` file is written beside the compiled HTML and copied to exports when rendering. The video also contains large caption overlays, rendered through the exact same deterministic timeline.

Important: the current subtitle cues use **phrase-level estimated timings proportional to words within each measured Kokoro scene audio duration**. They are NOT word-for-word timestamps, and they are not forced-aligned with actual phonemes. The resolved plan explicitly records `word_aligned: false`. Future accurate alignment should use a tested local forced-alignment engine rather than misleading estimates.

## Safety and compatibility
The JSON scene validator rejects unknown visual presets and injected fields. Visual SVG comes only from a fixed trusted library. Model-provided text is HTML-escaped. Omitting `visual` retains the original abstract scene treatment. Existing Gemini router and local speech interface are unchanged.

## Reproduction
```bash
npm ci
python -m pip install -r requirements-tts.txt
export HYPERFRAMES_PYTHON="$(command -v python)"
node_modules/.bin/hyperframes browser ensure
python -m unittest discover -s tests -v
python src/hyperframes_pipeline.py --plan examples/sky_blue_30s.json --out-dir build/v1_1/hyperframes --voice af_heart --tts --render --output build/v1_1/exports --fps 30
```

After verified GitHub CI, rendered samples are saved to `samples/v1.1-sky-blue` on branch `feature/v1.1-visual-scenes-captions`. Don't promote to main unless the genuine MP4 checks pass.
