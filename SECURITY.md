# Security and deployment scope

This release is a **single-user local demo**, not a multi-tenant booking service. Bind to `127.0.0.1`. All transports act as `demo-user`; an optional `BOOKING_API_TOKEN` is a shared bearer credential, not an authenticated customer identity. Domain ownership checks alone do not make the server multi-user safe.

The configured model provider receives prompts, tool arguments/results and conversation context through OpenAI by default or OpenRouter when selected. Google-backed evaluations send evaluation data to Google services. Use synthetic data when testing. JSON files and retained proposal/session history may contain names and appointment details and are not encrypted by the application. Protect the directory and do not commit it.

LLM tools cannot call the confirmation service. Human-facing clients must render exact proposal details and obtain user approval before calling the confirmation endpoint. The application cannot prove a human physically clicked a button; authorization enforcement by trusted clients is part of the boundary. Do not give an untrusted agent arbitrary authenticated REST access.

Before networked production deployment implement: authenticated users/tenants, trusted identity propagation across A2A, per-user authorization, HTTPS, rate/body limits, CSRF/origin controls for the intended browser auth model, retention/erasure, encryption/backups, persistent task state, distributed transactional storage and operational monitoring. See FUTURE.md.

Report vulnerabilities privately to the repository owner through an available private contact or GitHub private vulnerability reporting if enabled. Do not post credentials or customer records in public issues. Rotate any exposed credentials immediately.
