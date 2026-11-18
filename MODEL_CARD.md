# Model card — ADK booking agent

Version: 0.1.0 · Date: 2026-11-18 · Repository owner: atri703.

## System and models

Appointment assistant implemented in Python Google ADK. The booking specialist and optional coordinator use OpenAI **gpt-5.2**, via LiteLLM identifier `openai/gpt-5.2`, authenticated with `OPENAI_API_KEY`. The model alias is configurable; no weights are trained or fine-tuned. There are no embeddings, vector database or retrieval corpus.

Google-backed evaluation uses ADK/Agents CLI's separately configured judge and simulated-user models. They are not the main booking model. Actual judge/simulator IDs must be captured from executed runs; no Google model evaluation has been claimed from offline tests.

## Intended use

Local demonstrations of appointment discovery, proposals, explicit confirmation, CRUD, persistent conversation, and A2A integration. The service supports one resource and one demo user, weekdays 09:00–17:00, 30/60-minute durations and a 90-day horizon. Inputs are text or structured JSON; outputs are natural-language responses, proposals and stored booking results.

Not intended for public multi-tenant deployment, emergency/medical triage, payments, autonomous unreviewed commitments, or reliable external calendar synchronization.

## Data and provenance

All committed tests and examples are synthetic. `data/bookings.json` is an empty seed-format document. The 36 reviewed scenarios are hand-authored; they are regression tests, not a statistically representative benchmark or held-out evaluation population. No synthetic model-generated traces are represented as already generated.

Live chat transmits messages and relevant tool data to OpenAI. Google simulation/judging processes evaluation inputs and traces through Google services. Local JSON stores can contain personal data; no application-level encryption or automatic retention/erasure is implemented. Cancellation deletes the active booking but retained proposals/session history may still contain its data.

## Evaluation methodology

- Deterministic unit and integration tests cover JSON/SQLite transaction parity, overlap prevention, version conflicts, ownership at the service layer, idempotence, expiry, rollback, session recovery, REST and A2A.
- Scripted models exercise the actual ADK runner and coordinator-to-specialist transport without model API calls.
- Offline ADK Eval verifies evaluator/tool-trajectory wiring.
- Live fixed scenarios use an isolated store per case, a fixed clock and final-state assertions.
- Optional Google-backed rubric grading and synthetic multi-turn evaluation assess response quality and task/tool behavior.

| Measure | Result |
|---|---|
| Offline deterministic/framework checks | See docs/VALIDATION.md for executed results |
| GPT-5.2 live regression score | Not evaluated; no OpenAI key supplied |
| Google synthetic conversations/grading | Not evaluated; Google credentials/project not supplied |
| Real-world booking success/fairness | Not evaluated |
| Latency/token usage/cost | Not benchmarked |

A passing offline suite is not evidence that the model passes adversarial requests or the live regression suite. Initial 0.9 rubric thresholds are proposed acceptance gates, not measured scores.

## Risks and mitigations

Hallucinated dates/results, ambiguous natural-language requirements, prompt injection, provider outages and excessive calls remain possible. Mitigations include strict schemas, tool-sourced facts, code-enforced hours/versions/conflicts, a bounded chat run, explicit proposal review and no model-accessible commit function. The user must verify exact proposal details. Service ownership is tested, but the demo transport uses one fixed identity and is not multi-user authentication.

## Operations and change control

Keep secrets outside source control. Use runtime storage backups and review policies before real data use. Re-run deterministic and live evaluations after model/prompt/tool/dependency changes. Regenerate Agent Card and evaluation exports after changing contracts. Pin a provider snapshot if a stable model revision is required and re-evaluate it. See SECURITY.md, AGENTS.md and FUTURE.md for deployment and governance work still required.
