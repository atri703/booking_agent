# Architecture decisions

## ADR-001: JSON first, database dormant

The user requested clone-and-test operation without a database. JSON is the only runtime backend. A tested SQLite implementation shares the transaction contract but is not wired to runtime configuration. Whole-document storage keeps the demonstration understandable; normalized PostgreSQL belongs in a future migration.

## ADR-002: Human confirmation outside the LLM

A language model cannot establish user authorization merely by producing a boolean. Agent tools prepare proposals; a trusted client reviews and confirms the exact stored payload. This prevents tool-calling prompts from skipping approval and enables idempotent retries. Consequence: natural-language yes does not complete a booking, and A2A consumers need a confirmation UI/REST integration.

## ADR-003: Pin and test A2A 1.0

ADK 2.14.1 with a2a-sdk 1.3.1 serves the A2A 1.0 card and JSON-RPC schema. Older tutorials use different fields/methods. Generate the card from the installed SDK and test actual requests and RemoteA2aAgent delegation. Do not manually convert a model card into an Agent Card.

## ADR-004: Separate evaluation evidence

Offline tests prove deterministic behavior/framework wiring. Live OpenAI inference and Google-backed simulation/judges are separate, credential-dependent runs. Fixed cases use fresh storage and a fixed clock. Synthetic cases are reviewed before promotion; never claim generated/live success from a schema-only check.

## ADR-005: Spec Kit is development tooling

Specify CLI 1.4.2 initializes actual Codex and Claude integrations. It guides repository evolution, not runtime booking reasoning. The core specification, constitution and tasks are checked in. No separate GSD product is installed.
