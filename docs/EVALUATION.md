# Evaluation guide

## What each layer proves

| Layer | Credentials | Evidence |
|---|---|---|
| pytest + scripted ADK/A2A integration | None | Domain rules, protocol wiring, restoration, storage parity |
| Offline ADK Eval smoke | None | Real ADK evaluator runs a tool-trajectory assertion against a scripted model |
| Live ADK fixed scenarios | Selected provider key | Configured model tool paths where specified and final-state/proposal assertions |
| ADK rubric judge | Selected provider key plus Google model access | Conversational correctness, confirmation handling and helpfulness |
| Agents CLI synthesis/grading | OpenAI plus Google auth/project/services | Newly generated multi-turn scenarios, traces and managed scores |

The model under test defaults to GPT-5.2. `BOOKING_MODEL` may select an OpenRouter model for the fixed ADK runs. Google judges/simulators are separate dependencies; an OpenAI or OpenRouter key is insufficient for them. Their default model names are owned by the pinned ADK/Agents CLI packages and can change with upgrades. Record them from the evaluation run when reporting results.

## Prewritten data

`tests/eval/scenarios.json` contains **36 reviewed cases**, including five multi-turn conversations. Cases cover policy, availability, boundary dates/hours, listing, proposals, missing details, ambiguity, prompt injection, existing bookings, rescheduling, cancellation and changed preferences.

`python -m scripts.build_eval_sets` exports:

- `tests/eval/adk/booking.evalset.json`: ADK EvalSet.
- `tests/eval/datasets/booking.json`: Google evaluation SDK EvaluationDataset.

Tests parse both with the actual installed SDK schemas. The formats are deliberately separate. The CLI export carries conversation input and behavior notes; the custom ADK runner is authoritative for fixture seeding and per-case state assertions. Do not run the entire exported file against a shared mutable production store.

## Reproducible ADK runs

For the default model, set `OPENAI_API_KEY` locally. To evaluate through OpenRouter without an
OpenAI key, put the following in the untracked `.env` file:

```dotenv
OPENROUTER_API_KEY=<my key, set locally>
BOOKING_MODEL=openrouter/nvidia/nemotron-3-ultra-550b-a55b:free
```

Then run the same commands:

```bash
uv run --no-sync python -m scripts.run_adk_eval --offline
uv run --no-sync python -m scripts.run_adk_eval --case create_30
uv run --no-sync python -m scripts.run_adk_eval
uv run --no-sync python -m scripts.run_adk_eval --judge
```

Each case gets a fresh temporary JSON store, a fixed clock (`2030-01-07T00:00:00Z`), and a synthetic existing booking only when specified. The runtime server still uses the real clock. No live booking dataset is reset or used. Tool trajectories use IN_ORDER matching so additional relevant calls are allowed; important tool arguments still must match.

After ADK runs the conversation, the wrapper checks the actual store: bookings must be unchanged until explicit client confirmation, and proposal count must match the case. Mutation behavior is tested separately through REST/domain tests. Negative/clarification scenarios without an expected path use final-state assertions in the non-judge profile; they are **not automatically judged for language quality** in that profile. Use `--judge` to assess response quality. Acceptance thresholds are initial targets, not empirical accuracy claims.

Reports: `artifacts/adk-offline.json` or `artifacts/adk-live.json`. A failed case causes nonzero exit. Offline mode is clearly labeled `offline-scripted`; live reports record the selected `BOOKING_MODEL` identifier.

ADK CLI can also run the isolated evaluation entry point:

```bash
uv run --no-sync adk eval eval_agent tests/eval/adk/booking.evalset.json:policy \
  --config_file_path tests/eval/adk/test_config.json --num_runs 1 --parallelism 1
```

The wrapper is preferred for the full suite because it seeds and isolates each case. Direct `adk eval` uses `eval_agent`, a fixed clock and `artifacts/eval-runtime`; it does not automatically create each case's fixtures. ADK Web/CLI sessions are managed by those tools, while the application server uses our JSON session service.

## Google authentication

For Vertex-backed synthesis, configure a Google Cloud project with billing and the evaluation/model services available to your identity. Authenticate using the supported Agents CLI interactive login or Google Application Default Credentials (`gcloud auth application-default login`) and set `GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION=global`, and `GOOGLE_GENAI_USE_VERTEXAI=TRUE`. These are separate from the OpenAI or OpenRouter key used by the agent under test. No credentials belong in the repository.

For ADK's Google LLM judges, configure supported Google model credentials (Vertex ADC/project/location, or the supported Gemini API-key mode). Google services and model availability depend on the account and region. Check docs/SOURCES.md and installed CLI help if upgrading.

## Generate new conversations

```bash
uv run --no-sync python -m scripts.synthesize_evals --count 10 --max-turns 8 --grade
```

The script invokes the actual pinned `agents-cli eval dataset synthesize` command with booking-specific instructions. It uses `eval_agent` and a disposable JSON directory, bounds scenario count/turns, then optionally invokes `agents-cli eval grade`. The simulator's goal is a valid reviewed proposal, not a confirmed booking: it cannot authorize the human confirmation endpoint.

Output is `artifacts/synthetic-traces.json`. Each generated trace contains the scenario plus simulated user/agent/tool events. Synthesis is experimental and needs Google authentication. **No model-generated dataset is supplied as if it had been executed**; only hand-authored reviewed cases are committed. Run synthesis with credentials, inspect its failures, redact content, and promote useful cases into the reviewed scenario file.

The multi-turn grading configuration selects `multi_turn_task_success`, `multi_turn_tool_use_quality`, and `multi_turn_trajectory_quality`, with initial thresholds of 0.9. Do not apply single-turn-only metrics to these multi-turn traces. Strict reference trajectories are evaluated with fixed ADK cases, not dynamic user simulation.

## CI and interpretation

Ordinary CI does not contact a model. The separate manually triggered live workflow remains configured for the default model and requires `OPENAI_API_KEY`; use the commands above for local OpenRouter evaluation. Google synthesis is not automatically triggered. A passing offline build does not mean the selected model passed the live cases. Keep generated traces out of source control; they can contain personal data, prompts and tool results.
