# Booking Agent Constitution

Version 1.0.0 · Ratified 2026-11-18.

1. Local usability: a fresh clone must exercise JSON CRUD without cloud credentials or a database server.
2. Explicit authorization: models can propose changes; a trusted client confirms the exact stored proposal. Never expose a model commit tool.
3. Transaction correctness: conflict and version checks occur atomically with writes; retries are idempotent and failures preserve existing records.
4. Verifiable interoperability: pin dependencies, generate the A2A card from the SDK and test real protocol traffic.
5. Honest evaluation: separate offline wiring, live OpenAI inference and Google simulation/judging. Do not invent results.
6. Privacy: commit no secrets, runtime data, customer records or raw evaluation traces.
7. Maintainability: keep schemas, tools, domain rules, storage and transport separate; update specs and tests with behavior changes.
8. Database migration is explicit future work; the tested database adapter remains disconnected until requested.

Changes to these principles require an explicit specification/decision update and regression review.
