# Repository instructions for coding agents

Read README.md, ARCHITECTURE.md, SECURITY.md and the relevant spec before changing behavior. CLAUDE.md points here; keep one authoritative engineering policy.

## Non-negotiable behavior

- JSON remains the default and only runtime storage until explicitly requested otherwise. Do not activate SQLite/PostgreSQL simply because adapter code exists.
- Model tools can read/propose, never commit mutations. Preserve explicit client confirmation, immutable proposals, expiry, replacement and idempotent retry semantics.
- Recheck conflicts and versions inside the write transaction. Never split read/check/write across separate transactions.
- Preserve local clone-and-run operation without API keys. Model credentials may only be required for chat/live evaluation.
- Keep model configuration on `openai/gpt-5.2` unless the user requests a change.
- A2A is 1.0 for the pinned SDK. Do not copy 0.3 card/request examples into this code.
- Never commit secrets, real customer records, runtime JSON, traces or .env files.
- Do not claim offline mocks prove live model behavior, deployment, or synthetic-evaluation success.

## Workflow

1. Read the current code and latest official docs for changed APIs; record compatibility changes in docs/SOURCES.md.
2. Use the installed Spec Kit workflow: constitution → specify → plan → tasks → implement → converge. Codex skills are in .agents/skills; Claude skills in .claude/skills.
3. Update the spec/contracts first for behavioral changes, then implement a focused change.
4. Add meaningful boundary/regression tests. Reuse adapter parity tests for storage changes.
5. Run the checks below before committing; fix actual failures. Do not weaken tests or thresholds to hide a failure.
6. Update model/evaluation documentation for changes to prompts, models, tools or policy.

```bash
uv sync --locked --all-extras
uv run --no-sync ruff check booking_agent coordinator eval_agent scripts tests
uv run --no-sync ruff format --check booking_agent coordinator eval_agent scripts tests
uv run --no-sync python -m pytest -q
uv run --no-sync python -m scripts.demo_crud
uv run --no-sync python -m scripts.run_adk_eval --offline
uv run --no-sync python -m scripts.build_eval_sets
uv run --no-sync python -m scripts.export_agent_card
```

Inspect the diff after regenerating artifacts. Preserve the upstream license. Keep .specify, .agents and .claude toolkit assets separate from application code; do not run application lint over vendored toolkit scripts. Add dependency changes through pyproject.toml and regenerate uv.lock.

## Where to change things

- Rules: booking_agent/service.py and models.py.
- Tool descriptions/prompt: booking_agent/tools.py and agent.py.
- Persistence: booking_agent/storage/ and sessions.py.
- Transport and auth: booking_agent/server.py; coordinator/agent.py.
- Reviewed eval scenarios: tests/eval/scenarios.json, then regenerate exported schemas.
- Google synthetic scenarios: scripts/synthesize_evals.py; never edit generated traces into claims of measured quality without review.

## Completion evidence

Report the actual tests run, CI link/status, commit, and any unverified integration. Live OpenAI calls spend money. Google synthesis needs its own credentials. Keep scheduled/automatic billing out of ordinary PR CI.
