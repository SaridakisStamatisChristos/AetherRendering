# AetherRendering v1.5 — Articulated IK and hand-object choreography

Development branch: `feature/kinematic-actions-v1.5`. Based on the real-rendered v1.4 checkpoint, preserving its Gemini/Kokoro/HyperFrames pipeline, seven classic/cinematic scenes, three v1.4 action types and 30/60 fps output.

## Concrete improvements

**Two-bone arm IK**: Python solves the law-of-cosines elbow position for each target hand location, using measured fixed limb lengths. No freeform model-generated skeleton coordinates. Impossibly distant IK targets are rejected.

**Hand/object correspondence**: A carried battery's translation matches the hand's contact-to-carry motion exactly (−40 horizontal, −75 vertical units). Its position is kept inside an animated outer group while a non-animated SVG translation anchor preserves placement.

**Articulated legs**: Two-link legs have distinct knees and moving feet. A short alternating walk cycle is coordinated with the actor's transition across the frame. This is stylized keyframed walking, not a foot-locked motion-capture solver.

**5 actions**: `walk_to`, `pick_up`, `inspect`, `set_down`, and `operate`. Each has separate, absolute-time, seekable GSAP keyframes.

**Camera and narrative**: The five previously implemented safe camera options and timed 2–4 label beats remain available. The scene timing follows actual measured Kokoro WAV audio.

## New JSON contract

```json
{
  "type":"kinematic_stage",
  "prop":"battery",
  "behavior":"pick_up",
  "camera":"push_in"
}
```

Only known `prop`, `behavior`, `camera`, and `type` keys are allowed. The renderer compiles deterministic SVG/GSAP, never executes an arbitrary JSON script.

## Real 5-shot demonstration

`examples/lamp_repair_ik_30s.json` contains original narration of a technician walking to a failed lamp, lifting and inspecting a battery, placing it onto the bench, and operating the lamp. Scenes intentionally vary their camera setting.

```bash
npm ci
python -m pip install -r requirements-tts.txt -r requirements.txt
export HYPERFRAMES_PYTHON="$(command -v python)"
python -m unittest discover -s tests -v
python src/hyperframes_pipeline.py \
  --plan examples/lamp_repair_ik_30s.json \
  --out-dir build/kinematic15/hyperframes \
  --voice af_heart --tts --render --fps 60 \
  --output build/kinematic15/exports
```

Dedicated CI: `.github/workflows/kinematic-actions-v1.5.yml`, including strict validation, a real spoken portrait and landscape video, 60 fps, decoded AAC audio, and 15 sampled frames per format with change measurements. Successful MP4s and visual contact sheets are published under `samples/lamp-repair-v1.5/`.

## Meaningful limitations

The elbow and knee positions are solved exactly **at authored key poses**. GSAP interpolates between them; this is not a continuously constrained rig with exact limb lengths between every frame. Walking is stylized and does not implement physically planted feet. Hand-object contact is geometrically aligned for selected behaviors, not general physics collision or arbitrary object grasping. Each scene has an independent illustrative pose rather than persistent physical world state across cuts. No 3D, real lip-sync, source AI video model, or third-party assets are required. Automated image-change checks do not guarantee artistic quality.
