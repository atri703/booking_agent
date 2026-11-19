# Feature: JSON-backed A2A appointment agent

Status: implemented local demonstration; live model evaluation pending credentials.

## User stories

- As a developer, clone the repository and exercise create/read/update/delete with no model key or DB server.
- As a user, ask about appointments, supply missing information, inspect an exact proposal and confirm it.
- As a user, refresh or restart the server and resume the stored conversation.
- As another agent, discover the booking Agent Card and request work through A2A.
- As a maintainer, use Spec Kit and coding-agent docs to safely extend the project.

## Acceptance criteria

FR-01: JSON is the only runtime storage; a database adapter exists but is inactive.
FR-02: Support create, list/get, update and delete through validated proposal/confirmation operations.
FR-03: Reject past/out-of-hours/off-grid/unknown-resource/overlapping bookings; 90-day horizon.
FR-04: Recheck conflicts/version at commit; replay a successful confirmation without duplicate mutation.
FR-05: Changed details supersede old proposals; pending proposals expire in ten minutes.
FR-06: Persist ADK conversation events/state in JSON and reject stale session updates.
FR-07: Main LLM defaults to GPT-5.2 through OpenAI and ADK LiteLLM; operators may select
an OpenRouter model with `BOOKING_MODEL` and its provider-specific API key without changing
offline CRUD behavior.
FR-08: Serve and validate A2A 1.0 Agent Card/RPC; include a remote coordinator/client.
FR-09: Include model card, architecture, API, evaluation, future and coding-agent documentation.
FR-10: Include at least 30 reviewed cases, ADK evaluation code and actual Agents CLI synthesis invocation.
FR-11: Ordinary CI tests deterministic behavior and framework wiring without paid keys.
FR-12: State the single-user demo boundary and incomplete live evaluation explicitly.

## Out of scope

Public multi-tenant hosting, voice, payment, notification/calendar integrations, distributed persistence, automatic Google billing, and a separate GSD toolkit.
