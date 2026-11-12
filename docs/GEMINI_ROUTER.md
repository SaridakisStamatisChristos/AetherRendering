# AetherRendering — Gemini Model Router

This is an additive upgrade: the existing HyperFrames/Kokoro composition and FFmpeg fallback renderers remain unchanged.

## Usage

Open **Actions → AI Video — HyperFrames + Kokoro → Run workflow**. Choose `gemini`, leave `model=auto`, and optionally set `complexity=auto|simple|standard|complex`. The router queries Gemini's live `models.list` endpoint using your `GEMINI_API_KEY` GitHub secret, filters for configured models supporting `generateContent`, and tries candidates in priority order. A manually supplied `model` disables model fallback and must appear in the router config.

Local CLI:

```bash
export GEMINI_API_KEY='your-key' # Never commit a key
python src/ai_director.py --topic 'Quantum computing explained' --provider gemini \
  --model auto --complexity auto --duration 30
# Optional: list text-generation model IDs exposed by the key
python src/ai_director.py --topic 'unused' --list-models
```

## Policy and model configuration

Edit `config/gemini_router.json` to change the preferred models for simple/standard/complex work. Models must also be listed in `models`, enabled, and returned by Gemini's live discovery response. Non-text models (e.g. image, live speech) are not automatically routed into JSON video planning.

`max_requests_per_day`, `max_requests_per_minute`, `max_tokens_per_minute` are **your own protective caps**. Their initial `null` value means **no local cap**, *not* unlimited Google quota; Google's live project quotas still apply. Enter your **actual project-specific limits** from [AI Studio](https://aistudio.google.com/). `max_output_tokens` bounds model output per request; do not exceed a model's actual supported max.

Daily counts reset at **midnight America/Los_Angeles**, matching Google's documented request-per-day reset. Minute token consumption uses conservative character-to-token estimates before calling Google and actual response usage, including thinking tokens when reported, when available. Actual Google tokenization may differ. To prevent overshooting, use a margin below your real quotas. A 429 triggers a temporary cooldown and routing to another allowed model. API authentication/permission errors (401/403) fail closed and **do not rotate models**.

The router records every attempted request (including failed ones) in `state/gemini_usage.json` and writes a redacted result to `build/gemini_router_audit.json`. It does not log API keys or prompts. A GitHub Actions step commits the ledger before rendering so rendering failures do not erase its counts. Runs are serialized using a workflow concurrency group. **This ledger cannot see usage from other applications or API keys in your Google project**, and local runs need to synchronize their state if they share one quota.

## Caveats

- No live Gemini call is possible until the Actions secret exists. Offline unit tests use mocked API responses.
- New model discovery does not confer quota or billing entitlement: Google may reject a model despite listing it.
- Preview/paid models can incur charges. `gemini-3.1-pro-preview` is included in configuration **disabled by default**.
- For cost control, you should consider adding a spend cap in Google AI Studio; the router does not enforce dollar-denominated charges.
- The system may render a video longer or shorter than the target because Kokoro's measured narration duration takes precedence.
- The workflow writes usage to `main`. If the branch is protected or another independent workflow uses the same API key concurrently, usage synchronization needs a central store or another backend.

Official docs: https://ai.google.dev/gemini-api/docs/models and https://ai.google.dev/gemini-api/docs/rate-limits
