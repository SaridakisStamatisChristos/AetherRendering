# AetherRendering v1.1 — layered visual scenes (development)

This release adds five **reusable** deterministic SVG visual templates:
`spectrum`, `particles`, `orbit`, `comparison`, `horizon`.

Unlike the previous all-typography version, each visual template draws animated objects and drives multiple GSAP timeline transitions, including entering elements, light beams, scattered rays, orbiting rings, comparative bars, and moving sunlight. The camera drifts subtly through each shot. No video generation API, image model or externally hosted picture is needed.

## Backward-compatible JSON extension

A scene may include an optional `visual` object. An old scene without `visual` is rendered as before. Example:

```json
{
  "title": "LIGHT MEETS AIR",
  "subtitle": "Tiny molecules redirect incoming light.",
  "narration": "Blue light is scattered by small molecules.",
  "duration": 6,
  "motion": "rise",
  "visual": { "type": "particles" }
}
```

Comparison supports safe simple labels and normalized illustrative values:

```json
{"type":"comparison","labels":["VIOLET","BLUE","RED"],"values":[0.95,0.78,0.25]}
```

Labels are escaped, and user-provided executable code or external asset URLs are not accepted. Values are illustrative for layouts, not scientific measurements; fact-check the generated story.

## Rendering

Install as documented in the root README, then run:

```bash
python src/hyperframes_pipeline.py --plan examples/sky_blue_rich_30s.json \
  --out-dir build/rich/hyperframes --tts --render --fps 60 \
  --output build/rich/exports
```

The default remains 30 fps, and `--fps 60` now updates both composition metadata and HyperFrames rendering rate. Run the branch workflow `visual-scenes-v1.1.yml` for a genuine 60 fps, Kokoro narrated portrait and landscape comparison sample. Watch the video for artistic quality; passing codec/audio checks alone cannot certify it.

**Not yet built:** imported photos/footage, lip-sync character rigs, shot transition editing, music/SFX, word-level captions, and integrated AetherMotion/AetherPaper adapters.

## Real execution evidence — verified 13 November 2026

[Successful GitHub Actions run](https://github.com/SaridakisStamatisChristos/AetherRendering/actions/runs/43413982958) established:
- **30 Python tests passing**, including legacy compatibility, strict visual config and comparison-input safety.
- **29.83-second** portrait video, 1080 × 1920, **60 fps**, AAC audio mean −22.7 dB.
- **29.83-second** landscape video, 1920 × 1080, **60 fps**, AAC audio mean −22.7 dB.
- Both files passed full FFmpeg decoding and were committed on the experimental feature branch.

[Download enhanced portrait MP4](https://raw.githubusercontent.com/SaridakisStamatisChristos/AetherRendering/feature/visual-scenes-v1.1/samples/sky-blue-rich/portrait-60fps.mp4)

[Download enhanced landscape MP4](https://raw.githubusercontent.com/SaridakisStamatisChristos/AetherRendering/feature/visual-scenes-v1.1/samples/sky-blue-rich/landscape-60fps.mp4)

This establishes that the richer video renders correctly. It does **not** establish editorial/artistic approval. The feature has not been merged into main pending visual review.
