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

## Real rendering verification — 13 November 2026

[Final successful GitHub Actions run](https://github.com/SaridakisStamatisChristos/AetherRendering/actions/runs/43453296273) passed 52 Python tests, rendered **two 32.75-second MP4s** at **60 fps**, measured genuine Kokoro voice audio at −22.6 dB mean (AAC), and verified full FFmpeg decoding, resolution and sound.

| Video | Resolution | Duration | Size |
|---|---|---|---|
| [Portrait MP4](https://raw.githubusercontent.com/SaridakisStamatisChristos/AetherRendering/feature/character-actions-v1.4/samples/solar-power-v1.4/portrait-60fps.mp4) | 1080×1920 | 32.75 seconds | 10,517,354 bytes |
| [Landscape MP4](https://raw.githubusercontent.com/SaridakisStamatisChristos/AetherRendering/feature/character-actions-v1.4/samples/solar-power-v1.4/landscape-60fps.mp4) | 1920×1080 | 32.75 seconds | 10,288,443 bytes |

**Motion proof:** [Portrait contact sheet](https://raw.githubusercontent.com/SaridakisStamatisChristos/AetherRendering/feature/character-actions-v1.4/samples/solar-power-v1.4/contact_sheet.png) and [landscape contact sheet](https://raw.githubusercontent.com/SaridakisStamatisChristos/AetherRendering/feature/character-actions-v1.4/samples/solar-power-v1.4/contact_sheet_landscape.png) contain three sampled frames from each of five scenes (30 samples total), with nonzero frame change measured for every scene in both formats.

**Visual repair:** The first technically valid sample exposed a real composition problem: object icons left their flow-node positions, and a lamp close-up shifted out of its focal area. The root cause was animating scale and translation on the same SVG group. The final version uses an unanimated outer translation anchor and applies GSAP to an inner group. The repaired videos were rendered again, and both contact sheets visually inspected to confirm that the objects stay placed correctly. Three regression tests protect against this recurrence.

The video is a **stylized procedural 2D animation**; presenter limbs use predefined joints, not character physics, inverse kinematics or a full 3D rig. This is a reusable engine milestone, not yet a professional animation film. Keep it in the separate development branch until its illustration style is accepted.
