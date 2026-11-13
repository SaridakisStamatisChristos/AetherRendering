# AetherRendering v1.4 — Character actions and object narratives

This experimental branch extends verified v1.3. It keeps the Gemini router, Kokoro/HyperFrames pipeline, 30/60 fps selection, seven earlier visual templates and the 15-animated-beat grammar. No extra AI generation provider or commercial asset package is necessary.

## New reusable animation capabilities

- **character_stage**: A consistent 2D illustrated presenter rig, with animated head, blinking eyes, arms, jacket and legs. Its motions include `introduce`, `point`, `lift`, `operate`, and `celebrate`.
- **object_chain**: Safe 2–4 object narratives, sequentially revealed with connecting arrows to demonstrate flow and interaction.
- **product_focus**: A large hero object with controlled entrance, depth cues and orbiting highlights.
- **Camera presets:** `wide`, `push_in`, `pan_left`, `pan_right`, `detail`. Camera moves are deterministic GSAP timeline instructions.
- **Built-in props:** `sun`, `solar_panel`, `battery`, `lamp`, `gear`, `book`, `box`.

All new visuals are native SVG and generated locally. No network images or untrusted user-authored JavaScript are accepted. Character actions are stylized articulated SVG movements, not rigged 3D characters, motion capture or real lip synchronization.

## JSON examples

```json
{"type":"character_stage","prop":"solar_panel","action":"point","camera":"wide"}
```

```json
{"type":"object_chain","items":["sun","solar_panel","battery","lamp"],"camera":"pan_right"}
```

```json
{"type":"product_focus","prop":"lamp","camera":"detail"}
```

The new visual contract is strictly validated. Previous SVG styles and storyboards are unchanged.

## Full demonstration

An original five-scene solar-power explainer uses 15 micro-reveals, presenter interaction, an object-flow chain, a hero light bulb, four different camera movements, genuine Kokoro narration and 60 fps portrait/landscape MP4 rendering.

```bash
npm ci
python -m pip install -r requirements-tts.txt -r requirements.txt
export HYPERFRAMES_PYTHON="$(command -v python)"
python -m unittest discover -s tests -v
python src/hyperframes_pipeline.py \
  --plan examples/solar_power_actions_30s.json \
  --out-dir build/actions14/hyperframes \
  --voice af_heart --tts --render --fps 60 \
  --output build/actions14/exports
python src/visual_qc.py --video build/actions14/exports/vertical.mp4 \
  --resolved-plan build/actions14/hyperframes/resolved_plan.json \
  --output build/actions14/visual_qc
```

The dedicated `.github/workflows/character-actions-v1.4.yml` checks Python regression tests, final H.264/AAC dimensions, exact 60 fps, two 30-second-class video exports, and separate 15-frame motion contact sheets for portrait and landscape. It publishes videos to `samples/solar-power-v1.4` only if all gates pass.

## Limitations and artistic review

The presenter is a reusable vector illustration, not a human video actor or high-detail 3D model. The motions are predefined and approximate rather than true inverse-kinematics grasping. Model-generated scene semantics still require editorial fact-checking. User visual review is required before this branch should be merged into `main`.
