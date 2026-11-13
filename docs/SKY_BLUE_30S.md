# AetherRendering — 30-second narrated test

Topic: **Why the sky is blue**. Source JSON: examples/sky_blue_30s.json.

Original educational script for the existing AetherRendering engine, using the five supported motion presets. The storyboard targets 30 seconds; measured Kokoro speech determines the actual duration.

GitHub Actions uses pinned HyperFrames, local Kokoro ONNX, portrait and landscape H.264 rendering, FFmpeg full decoding, and audio audibility validation.

After a successful workflow, the real MP4s will be saved in samples/sky-blue-30s/ on the feature/sky-blue-30s-demo branch.

This tests the existing animated typography engine, not richer illustrations or characters.