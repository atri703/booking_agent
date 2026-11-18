# Future work

## Before a public multi-user deployment

1. Authenticate customers and agents; propagate server-verified tenant/user identity across REST and A2A. Remove the demo identity.
2. Migrate from local JSON to a normalized PostgreSQL schema with transactional overlap constraints and tested migrations. Preserve the proposal/confirmation contract. SQLite is included only as a parity-tested reference.
3. Persist A2A tasks, configure tenant-scoped session storage and distributed session concurrency.
4. Add retention, erasure, backups, encryption, rate limits and operational dashboards. Bound proposal/session history growth.
5. Run live GPT-5.2 regression and Google simulation/judging; review failures, set measured baselines and validate with a separate held-out dataset.

## Product extensions

- Configurable resource calendars, holidays, varying service durations and booking windows.
- External calendar adapters with retry/outbox reconciliation; never claim external success before confirmation.
- Email/SMS notifications with explicit consent and an outbox.
- Payments, cancellation policies, waitlists and admin workflows.
- Voice interface with interruption handling and session restoration, built on the same validated service.
- A2A authenticated confirmation extension with explicit signed approvals, if agent-to-agent committed booking is needed.
- Accessibility improvements and richer end-user UI; current interface is a manual test client.

## Engineering

- OpenTelemetry export and redacted structured audit streams.
- Prompt/model version comparison, repeated statistical evaluation and latency/cost budgets.
- Property-based scheduling tests, process-kill durability tests and multi-host integration environments.
- Normalize SQL tables and add a PostgreSQL adapter instead of scaling the single-row SQLite reference.

These items are planned, not implemented or deployed.
