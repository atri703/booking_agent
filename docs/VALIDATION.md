# Validation record

Local validation on 2026-11-18, Linux, Python 3.12.14, locked dependencies.

| Check | Observed result |
|---|---|
| pytest domain/API/session/SDK contracts | 61 passed |
| JSON and dormant SQLite parity | Included in pytest; CRUD, rollback, conflicts, ownership, expiry and retries passed |
| Real ADK runner with scripted model | Tool execution and persistent session recovery passed |
| A2A 1.0 discovery/SendMessage | Passed with scripted specialist |
| Coordinator → RemoteA2aAgent → specialist | Passed with scripted models and real ASGI transport |
| ADK Eval offline trajectory smoke | 1/1 passed |
| Offline create/read/update/delete demo | Passed against a temporary JSON file |
| Ruff lint and format | Passed |
| Python compile/import checks | Passed |
| ADK EvalSet, EvalConfig, Google EvaluationDataset and Agent Card schema validation | Passed |
| Python wheel and source distribution | Built successfully; HTML client included in wheel |
| Browser JavaScript syntax | Passed Node syntax check; manual visual browser review not performed |
| Docker image | Not built in this environment; Docker executable unavailable |
| Live GPT-5.2 inference/evaluation | Not run; OPENAI_API_KEY not configured |
| Google synthetic evaluation/judging | Not run; Google project/credentials not configured |

Two upstream deprecation warnings occur in ADK's AgentTool runner and the Google SDK's Pydantic models; they did not fail tests. No application warnings were suppressed to obtain passing results.

GitHub CI is independently triggered on push/PR and records its own results in the repository Actions tab. This file describes the local run and does not predeclare CI success. Offline tests exercise real framework code with scripted model responses; they are not a live-model quality benchmark.
