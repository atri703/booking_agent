# Technical plan

Use Python 3.12 (supported 3.11–3.13), Google ADK 2.14.1, LiteLLM 1.109.1, a2a-sdk 1.3.1 and GPT-5.2. FastAPI hosts REST/chat and mounts the ADK A2A application with its startup lifecycle. One Uvicorn worker and local disk are the supported deployment profile.

BookingService owns all domain logic. JsonStore supplies lock-protected transactions and atomic replace. SQLiteStore provides the same interface for future adoption and parity tests only. JsonSessionService implements the ADK session interface with persistent events/scoped state and stale-write detection.

Agent tools read or create proposals. Clients confirm via REST outside the model boundary. The optional coordinator delegates to the specialist using ADK RemoteA2aAgent through a real A2A connection.

Tests cover domain invariants, both adapters, REST, scripted ADK tool execution, sessions, live protocol wiring and schema validation. Separate runners cover fixed ADK cases, offline evaluator smoke, and real Google Agents CLI synthesis. Documentation distinguishes implemented, measured and future work.
