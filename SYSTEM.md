# Booking Agent System

## 1. What it does

The booking agent helps a single demo user check policy and availability, list appointments, and prepare proposals to create, reschedule, or cancel a booking through natural-language chat. It never treats chat as authorization: a booking changes only when a client displays the exact stored proposal, obtains explicit approval, and calls the confirmation API.

## 2. Architecture and approach choice

The system is a small hybrid agent: a FastAPI UI/API hosts a Google ADK `LlmAgent` through LiteLLM (OpenAI GPT-5.2 by default, with OpenRouter configurable), while Python tools delegate authoritative rules and state to a deterministic `BookingService`. The service stores bookings, proposals, audit entries, and ADK sessions in locked, atomically replaced JSON files; an optional coordinator reaches the specialist over A2A 1.0.

- **Prompting** fits conversation, detail collection, and tool selection, but prompting alone cannot guarantee ownership, conflict checks, version checks, or safe writes, so those rules remain in code.
- **Retrieval** does not fit the current problem: there is no document corpus to search, and booking facts are live structured state read through tools.
- **Fine-tuning** would add cost and stale learned behavior without enforcing transactions or authorization; the narrow, changing policy is clearer in prompts, schemas, and deterministic code.
- **An agent** does fit the multi-turn workflow because it can gather missing details and choose tools, but it is deliberately constrained to reads and immutable proposals rather than direct mutation.

## 3. Tools and permissions

| Agent tool | Permitted action |
|---|---|
| `booking_policy` | Read the clock, timezone, business hours, services, durations, horizon, and confirmation rule. |
| `find_available_slots` | Read calculated availability for a date and supported duration. |
| `list_my_bookings` | Read bookings owned by the fixed local identity, `demo-user`. |
| `propose_booking` | Validate details and store a create proposal for later human confirmation. |
| `propose_reschedule` | Validate ownership and expected version, then store an update proposal. |
| `propose_cancellation` | Validate ownership and expected version, then store a delete proposal. |

No model tool can confirm, create, update, or delete a booking. Only the client-facing confirmation route can call `BookingService.confirm`, which rechecks expiry, version, and conflicts inside the write transaction and makes duplicate confirmation idempotent.

## 4. Evidence and evaluation gates

The deterministic suite measures business-hour and time-zone boundaries, conflicts, ownership, proposal replacement/expiry, optimistic versions, idempotency, JSON transaction behavior, REST/chat behavior, and A2A wiring. The reviewed evaluation set contains 36 cases covering policy, availability, proposals, missing or ambiguous details, prompt injection, existing bookings, rescheduling, and cancellation; offline ADK evaluation proves framework and tool-trajectory wiring with a scripted model, not live-model quality.

Each live fixed case gets a fresh temporary store and fixed clock, then gates on expected tool order and important arguments where specified, expected proposal count, and the invariant that bookings remain unchanged without explicit confirmation; any failed case exits nonzero. Optional Google-backed grading separately measures multi-turn task success, tool-use quality, and trajectory quality against initial `0.9` thresholds. Ordinary CI remains offline and gates on lint/format, pytest, CRUD, scripted ADK evaluation, and generated-artifact checks; provider-specific live runs and Google judging are manual and must not be inferred from an offline pass.

## 5. First failure points under load or attack

Under real load, the first bottleneck is JSON persistence: every transaction locks and rewrites a whole document, HTTP chat relies on process-local session locks, the server is intended for one Uvicorn worker, and A2A task state is in memory. Multiple replicas would not share a safe transactional store or recover in-flight tasks, so production needs distributed persistence, durable task state, backups, and monitoring.

Against a hostile user, identity is the earlier security boundary: every transport acts as `demo-user`, and the optional bearer token is shared rather than user authentication. Prompt injection cannot directly commit through model tools, but an attacker with client/API access could abuse the confirmation boundary; network deployment therefore also requires authenticated tenants and trusted identity propagation, per-user authorization, HTTPS, rate/body limits, CSRF/origin controls, retention/erasure, and encryption. Model output may still be misleading, so stored service results—not prose—remain authoritative.
