# AetherRendering v1.3 — Cinematic visual refinement

This development branch follows the successfully verified v1.2 kinetic-storytelling implementation, preserving the original video engine, five prior SVG styles, Kokoro narration and backwards-compatible JSON.

## What's changed

- **Sky-dome illustration:** Blue photons visibly arrive at the viewer's eyes from separate atmospheric directions, replacing an unrelated orbital/globe metaphor.
- **Color perception illustration:** Qualitative violet/blue/red light paths enter a stylized eye, replacing an invented numerical comparison. No quantitative scientific claims are embedded in the illustration.
- **Multiple causal motions per scene:** White light, atmospheric scatter directions, viewer response and camera movement happen at different points across the real voice length.
- **Existing timed micro-beats and fades remain:** Fifteen story reveals across the 30-second educational script.

## Visual quality gate

Real render is sampled at 17%, 51%, and 83% of each scene (15 samples). A contact sheet is generated from decoded video frames, and per-scene average RGB frame differences are measured. The gate fails if any scene appears nearly static at all sample positions.

This motion gate does not replace manual aesthetic review; it establishes *measured temporal visual changes*. Full MP4 decoding, frame rate, resolution and genuine Kokoro/AAC audibility are still checked.

## Run

```bash
npm ci
python -m pip install -r requirements-tts.txt -r requirements.txt
export HYPERFRAMES_PYTHON="$(command -v python)"
python src/hyperframes_pipeline.py \
  --plan examples/sky_blue_cinematic_30s.json \
  --out-dir build/cinematic/hyperframes \
  --voice af_heart --tts --render --fps 60 \
  --output build/cinematic/exports
python src/visual_qc.py \
  --video build/cinematic/exports/vertical.mp4 \
  --resolved-plan build/cinematic/hyperframes/resolved_plan.json \
  --output build/cinematic/visual_qc
```

The dedicated GitHub workflow `.github/workflows/cinematic-visuals-v1.3.yml` executes this on a real runner and saves the new videos and contact sheet under `samples/sky-blue-cinematic/` only after all gates pass.

Live Gemini generation, word-level transcription, lip-sync, arbitrary imported footage and AetherMotion integration remain separate future work.
