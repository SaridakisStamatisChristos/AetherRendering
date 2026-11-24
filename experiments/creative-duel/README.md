# AetherRendering — native creative treatment

Both engines receive the identical brief and soundtrack. Native capabilities may be used freely; source artwork is independent rather than frame-matched. Brief: lonely robot crosses abandoned city, finds cyan pulse beneath sidewalk, awakens city at dawn. 15s / 720p / 24fps / H.264 with identical original music. No remote AI or commercial assets.

This AetherRendering variant is an original *three-chapter illustrated motion graphic*, using HyperFrames' seekable GSAP timeline, sweeping parallax, graphic editorial framing, gesture animation, an artifact pulse macro, SVG light rings, staggered relighting, and animated typography.

For a local run, from repository root:

```bash
npm ci
python3 experiments/creative-duel/scripts/make_creative_audio.py
mkdir -p experiments/creative-duel/scene/assets/{audio,vendor}
cp experiments/creative-duel/public/creative-score.wav experiments/creative-duel/scene/assets/audio/creative-score.wav
cp node_modules/gsap/dist/gsap.min.js experiments/creative-duel/scene/assets/vendor/gsap.min.js
node_modules/.bin/hyperframes browser ensure
cd experiments/creative-duel/scene
../../../node_modules/.bin/hyperframes lint
../../../node_modules/.bin/hyperframes render --output ../out/creative-aether.mp4 --fps 24
```

This experiment does not call Gemini or Kokoro because both renderers must use the same precommitted soundtrack to isolate visual composition and animation; the full integrated AI video pipeline needs a different end-to-end benchmark.
