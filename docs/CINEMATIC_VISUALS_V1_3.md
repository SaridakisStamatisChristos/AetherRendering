# AetherRendering v1.3 — Cinematic visual refinement

This development branch follows the successfully verified v1.2 kinetic-storytelling implementation, preserving the original video engine, five prior SVG styles, Kokoro narration and backwards-compatible JSON.

## What's changed

- **Sky-dome illustration:** Blue photons visibly arrive at the viewer's eyes from separate atmospheric directions, replacing an unrelated orbital/globe metaphor.
- **Color perception illustration:** Qualitative violet/blue/red light paths enter a stylized eye, replacing an invented numerical comparison. No quantitative scientific claims are embedded in the illustration.
- **Multiple causal motions per scene:** White light, atmospheric scatter directions, viewer response and camera movement happen at different points across the real voice length.
- **Existing timed micro-beats and fades remain:** Fifteen story reveals across the 30-second educational script.

## Visual quality gate

Both portrait and landscape videos are sampled at 17%, 51%, and 83% of each scene (30 samples total). A contact sheet is generated from decoded video frames, and per-scene average RGB frame differences are measured. The gate fails if any scene appears nearly static at all sample positions.

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

## Layout correction from real frame review

Inspection of the rendered 16:9 video revealed that the v1.3 story-beat strip overlapped part of the illustration. The subsequent layout revision moves the landscape illustration upward and seats the story strip below it. Portrait sizing remains unchanged. Both orientations now generate independent contact sheets and per-scene visual motion measurements so this class of issue can be reviewed explicitly.

## Real execution and visual inspection — 13 November 2026

The final validated code produced original, Kokoro-narrated H.264 MP4 exports:

| File | Resolution | Frame rate | Length | Bytes |
|---|---|---|---|---:|
| [Portrait MP4](https://raw.githubusercontent.com/SaridakisStamatisChristos/AetherRendering/feature/cinematic-visuals-v1.3/samples/sky-blue-cinematic/portrait-60fps.mp4) | 1080×1920 | 60 fps | 29.83s | 9,465,485 |
| [Landscape MP4](https://raw.githubusercontent.com/SaridakisStamatisChristos/AetherRendering/feature/cinematic-visuals-v1.3/samples/sky-blue-cinematic/landscape-60fps.mp4) | 1920×1080 | 60 fps | 29.83s | 9,182,959 |

Each has actual AAC audio with measured mean level **−22.7 dB**, passed full FFmpeg decoding and had correct video dimensions and frame rate. All **42 Python tests** passed.

Two [contact sheets](https://raw.githubusercontent.com/SaridakisStamatisChristos/AetherRendering/feature/cinematic-visuals-v1.3/samples/sky-blue-cinematic/contact_sheet.png) ([landscape sheet](https://raw.githubusercontent.com/SaridakisStamatisChristos/AetherRendering/feature/cinematic-visuals-v1.3/samples/sky-blue-cinematic/contact_sheet_landscape.png)) cover 15 sampled frames per orientation. The five scene-motion gates pass in **both** orientations. The landscape contact sheet uses a true horizontal thumbnail aspect ratio.

Real frame inspection revealed and then corrected a landscape overlap between the infographic illustration and lower narration-beat bar. The revised layout was independently inspected on decoded landscape frames. The [verified render pipeline](https://github.com/SaridakisStamatisChristos/AetherRendering/actions/runs/43424568598) passed all media/visual gates, but two parallel branch workflow jobs conflicted while committing large binaries. A [recovery verification/publishing workflow](https://github.com/SaridakisStamatisChristos/AetherRendering/actions/runs/43425796777) downloaded the exact validated original artifact, decoded both files again, checked 30 frame samples and committed the correct exports to the current branch head. No placeholder/synthetic audio was substituted.

The temporary recovery workflow was removed after successful publication; its commit and Actions run remain in Git history. CI's ordinary binary-publishing step should use an explicit branch-head refresh in future development to avoid concurrent binary rebase conflicts.

**Artistic note:** The result is now significantly stronger as narrated science infographics. It is still not a fully illustrated character animation or cinematic footage engine. Visual approval should precede merging this branch to main.
