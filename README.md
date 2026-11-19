# ADK booking agent

A clone-and-run appointment assistant using **Python ADK + OpenAI GPT-5.2 by default**, real **A2A 1.0** communication, persistent JSON conversations, and **JSON-file CRUD**. A small browser UI and REST API work without any model key. A tested SQLite adapter is included as future database code but **is not connected to the application**.

## Quick start

Requires Python 3.11–3.13 and [uv](https://docs.astral.sh/uv/getting-started/installation/). Python 3.12 is recommended. Run commands from the repository root.

```bash
git clone https://github.com/atri703/booking_agent.git
cd booking_agent
uv sync --locked --all-extras
uv run --no-sync python -m scripts.demo_crud
uv run --no-sync uvicorn booking_agent.server:app --host 127.0.0.1 --port 8001
```

Open **http://127.0.0.1:8001**. Choose a future weekday, find a slot, prepare a booking, inspect the proposal and confirm. Read, reschedule and cancel bookings from the same page. REST documentation: **http://127.0.0.1:8001/docs**.

This flow requires **no OpenAI key, Google credentials, database server, or cloud deployment**. The console demo uses its own temporary JSON file; the web app saves changes to `runtime/bookings.json`. `data/bookings.json` documents the empty starting format. The runtime creates an empty store automatically; no copying or migration is needed.

### Enable GPT-5.2 chat

Copy `.env.example` to `.env` (Windows PowerShell: `Copy-Item .env.example .env`) and set:

```dotenv
OPENAI_API_KEY=your-key
BOOKING_MODEL=openai/gpt-5.2
```

Restart the server and use the Chat section. The key stays on the server. The browser saves a conversation ID; JSON session history survives refreshes and server restarts. The default business timezone is `Asia/Kolkata`, configurable with `BOOKING_TIMEZONE`.

### Use OpenRouter for local chat

The existing ADK `LiteLlm` integration also accepts OpenRouter model identifiers. In your local
`.env`, leave `OPENAI_API_KEY` unset and configure:

```dotenv
OPENROUTER_API_KEY=<my key, set locally>
BOOKING_MODEL=openrouter/nvidia/nemotron-3-ultra-550b-a55b:free
```

Restart the server. Chat and the optional coordinator use the selected model; JSON CRUD still
works without either provider key. Never commit `.env` or an API key.

**Changes require the client's confirmation button or confirmation REST call.** Chat/A2A tools can prepare changes but cannot commit them. Saying “yes” in chat alone does not write data. This gives the user an exact, reviewable action and prevents model instructions from bypassing the write boundary.

### GCP deployment demonstration scaffold

[`deployment/gcp/`](deployment/gcp/README.md) contains a future deployment scaffold for the
ADK CLI's Agent Runtime/Agent Engine target and a private Cloud Run fallback for the external
OpenRouter/NVIDIA model path. This is **demonstration-only packaging**: it has been inspected
and tested locally, but no GCP credentials were available, none of its deployment commands
were executed, and no code has been deployed to Google Cloud. The cloud JSON filesystem would
be ephemeral and is not suitable for production persistence or multiple instances. Follow the
folder's Secret Manager and IAM instructions only in a billed demo project, and do not make
this single-user application public.

## Capabilities

- Find available 30/60-minute appointments, weekdays 09:00–17:00, up to 90 days ahead.
- Create, retrieve, update/reschedule, and delete/cancel bookings.
- Atomic JSON writes, cross-process file locks, optimistic versions, proposal expiry, and idempotent confirmation retries.
- Recheck availability inside the same locked transaction that commits a change.
- Persistent ADK events and conversation state in `runtime/sessions.json`.
- A2A booking specialist plus an optional GPT-5.2 coordinator using `RemoteA2aAgent`.
- Spec Kit 1.4.2 installed for Codex and Claude Code.
- 36 reviewed evaluation scenarios, ADK Eval runner, Google Agents CLI synthesis runner, and offline CI.

## Run the A2A coordinator

Keep the booking server running on port 8001. In another terminal:

```bash
uv run --no-sync adk run coordinator
```

The coordinator uses GPT-5.2 and calls the booking specialist over A2A. A simpler direct protocol client is also included:

```bash
uv run --no-sync python -m scripts.a2a_client "Show your booking policy"
```

Reuse `--context-id` with the returned `contextId` for follow-up A2A messages. The live Agent Card is at `/.well-known/agent-card.json`; `agent-card.json` is its committed reference export. Set `BOOKING_A2A_URL` to the externally reachable server URL when changing the host/port, and regenerate the reference with `python -m scripts.export_agent_card`. This version uses A2A **1.0**: JSON-RPC requests require `A2A-Version: 1.0`; older 0.3 payloads are not interchangeable.

A2A proposals include their ID and details. The consuming application should show them to the user and call the REST confirmation endpoint only after approval. A2A task status is in memory and is lost on server restart; persisted ADK conversations and bookings are separate. Do not promise task recovery after restart.

## Tests and evaluation

```bash
uv run --no-sync ruff check booking_agent coordinator eval_agent scripts tests
uv run --no-sync python -m pytest -q
uv run --no-sync python -m scripts.run_adk_eval --offline
# Live provider calls; fixed clock and fresh storage per scenario:
uv run --no-sync python -m scripts.run_adk_eval
# Select a single scenario:
uv run --no-sync python -m scripts.run_adk_eval --case create_30
```

Offline tests execute real ADK tools, A2A requests, the coordinator-to-specialist connection, JSON session restoration, and the ADK evaluation engine with scripted models. They do **not** measure live model quality.

Google-backed rubric grading and automatically synthesized conversations additionally require Google authentication and service access:

```bash
uv run --no-sync python -m scripts.run_adk_eval --judge
uv run --no-sync python -m scripts.synthesize_evals --count 10 --max-turns 8 --grade
```

See [EVALUATION.md](docs/EVALUATION.md) for exact credential requirements, metrics, isolation, and limitations. No synthetic cases or live model scores are claimed until those commands have actually succeeded.

## CI

[CI](.github/workflows/ci.yml) runs on every push and PR with Python 3.11 and 3.12: locked installation, lint, formatting, tests, offline CRUD, offline ADK Eval, generated contract checks, and package build. Ordinary CI needs no secrets.

[Live evaluation](.github/workflows/live-eval.yml) runs only when manually triggered and remains configured for the default OpenAI model and repository secret `OPENAI_API_KEY`. Local live evaluation may instead use the OpenRouter configuration above. Initial thresholds are acceptance targets, not measured model performance. Google-backed synthesis is run explicitly from the documented script so no Google billing happens during ordinary PR checks.

## Database code: included, disabled

`booking_agent/storage/sqlite_store.py` implements the same transaction interface and passes the same domain tests as JSON. It stores the versioned document in a SQLite transaction using `BEGIN IMMEDIATE`. This is a working reference adapter, not a normalized production database schema. The server always constructs `JsonStore`; there is intentionally no environment toggle that silently activates a database. See [database migration](docs/DATABASE.md).

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | unset | Enables GPT-5.2 chat and live agent inference |
| `OPENROUTER_API_KEY` | unset | Enables chat and live evaluation when `BOOKING_MODEL` starts with `openrouter/` |
| `BOOKING_MODEL` | `openai/gpt-5.2` | ADK LiteLLM model identifier |
| `BOOKING_DATA_DIR` | `runtime` | JSON data directory |
| `BOOKING_TIMEZONE` | `Asia/Kolkata` | Business hours and displayed dates |
| `BOOKING_RESOURCE` | `advisor` | Single bookable resource |
| `BOOKING_A2A_URL` | `http://127.0.0.1:8001` | Advertised A2A endpoint |
| `BOOKING_API_TOKEN` | unset | Optional shared demo bearer token |
| `GOOGLE_CLOUD_PROJECT` | unset | Google-backed evaluation only |
| `GOOGLE_CLOUD_LOCATION` | `global` in example | Google eval endpoint |

## Documentation and coding agents

- [Architecture](ARCHITECTURE.md): components, boundaries, persistence, failure behavior.
- [API](docs/API.md): complete JSON CRUD and A2A examples.
- [Evaluation](docs/EVALUATION.md): predefined tests, simulation, grading and reports.
- [Model card](MODEL_CARD.md): models, data, limitations, measured vs unmeasured results.
- [Future work](FUTURE.md): deployment, auth, PostgreSQL, voice and integrations.
- [AGENTS.md](AGENTS.md) and [CLAUDE.md](CLAUDE.md): instructions for later Codex/Claude changes.
- [Contributing](CONTRIBUTING.md), [security](SECURITY.md), [decisions](docs/DECISIONS.md), [sources](docs/SOURCES.md).
- [Specification](specs/001-booking-system/spec.md), [plan](specs/001-booking-system/plan.md), [tasks](specs/001-booking-system/tasks.md).

## Local-demo boundaries

All clients use one `demo-user` identity. The optional bearer token restricts entry but is **not multi-user authentication**. Run on loopback, with one server worker and a local disk. JSON locking is not a distributed database. Do not expose real customer data to public users until authenticated tenant identity, retention, encryption and production persistence are implemented. No payment, email, SMS or external calendar side effects are included.

## Troubleshooting

- **No slots:** choose a future weekday within 90 days; the whole appointment must end by 17:00 in the configured timezone.
- **409 conflict/stale/expired:** refresh the booking and generate a new proposal; do not retry with altered arguments under the old proposal ID.
- **503 chat:** set the API key named in the response (`OPENAI_API_KEY` by default or `OPENROUTER_API_KEY` for an `openrouter/` model); offline CRUD remains available.
- **401:** configure the same `BOOKING_API_TOKEN` in the UI/client and server.
- **A2A version error:** send the 1.0 header and payload shown in `scripts/a2a_client.py`.
- **Corrupt JSON:** stop the server and restore a known backup. The application intentionally does not overwrite corrupted storage.
- **Evaluation credentials:** OpenAI credentials do not authorize Google's simulator/judges. See the evaluation guide.

Docker example: `docker build -t booking-agent .`, then `docker run --rm -p 127.0.0.1:8001:8001 --env-file .env -v booking-data:/app/runtime booking-agent`. Docker packaging is supplied; check [validation](docs/VALIDATION.md) for what was actually executed.
