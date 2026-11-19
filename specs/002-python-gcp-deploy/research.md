# Research: Runnable Python GCP Deployment

## Decision: Use the pinned Agents CLI as the deployment engine

**Rationale**: `google-agents-cli==1.15.0` is already pinned. Its current deploy interface supports Agent Runtime and Cloud Run, Secret Manager references, environment variables, service identity, resource limits, instance limits, ports, private Cloud Run, preview, and status operations. A Python orchestrator can provide validation and a safe build context without duplicating Google deployment APIs.

**Alternatives considered**:

- Legacy `adk deploy agent_engine`: replaced because the repository asked for Agents CLI and the current CLI has the required target/security flags.
- Direct Agent Platform and Cloud Run client libraries: rejected because two evolving APIs would add dependencies and duplicate the pinned CLI's tested deployment logic.
- PowerShell wrappers: rejected because the requested deliverable is executable Python and the old scripts did not test context isolation.

## Decision: Generate an allowlisted temporary build context

**Rationale**: Cloud source deployment can upload every file in its context. Copying only `pyproject.toml`, `uv.lock`, the three packaged Python modules, and deployment-owned metadata prevents `.env`, runtime JSON, Git data, traces, and local tools from entering the upload regardless of ignore-file behavior.

**Alternatives considered**:

- Deploy directly from the repository root: rejected because it relies on ignore rules and retains the evaluation-oriented root Agents CLI manifest.
- Copy the entire repository then delete sensitive paths: rejected because denylist cleanup is easier to bypass when new files appear.

## Decision: Deploy the existing FastAPI/A2A service container

**Rationale**: The existing server already owns the booking service, confirmation boundary, JSON sessions, UI, REST, and A2A routes. The deployment Dockerfile changes only the container port and data directory configuration; application code remains unchanged.

**Alternatives considered**:

- Serialize only `root_agent`: rejected because that would omit the trusted REST confirmation client and create a second runtime behavior.
- Create a second cloud-specific agent implementation: rejected because it would duplicate prompts/tools and drift from local behavior.

## Compatibility sources

- Agents CLI deployment guide and CLI reference, checked 2026-11-19.
- Gemini Enterprise Agent Runtime deployment guide, checked 2026-11-19.
- Cloud Run source deployment documentation, checked 2026-11-19.
