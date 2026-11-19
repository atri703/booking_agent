# Implementation Plan: Runnable Python GCP Deployment

**Branch**: `002-python-gcp-deploy` | **Date**: 2026-11-19 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-python-gcp-deploy/spec.md`

## Summary

Replace the PowerShell/ADK scaffold with a tested Python CLI that creates a temporary allowlisted build context and invokes the pinned `google-agents-cli` deployment command for Agent Runtime or private Cloud Run. The default action performs a real deployment; `--preview` prints the safely rendered command and context manifest without contacting Google Cloud.

## Technical Context

**Language/Version**: Python 3.11–3.13; deployment image uses Python 3.12

**Primary Dependencies**: Python standard library, `google-agents-cli==1.15.0`, existing ADK/LiteLLM application dependencies

**Storage**: Existing JSON store under `/tmp/booking-agent` in cloud targets; ephemeral and single-instance only

**Testing**: pytest, Ruff, command/context tests with mocked subprocess execution

**Target Platform**: Gemini Enterprise Agent Runtime preferred; private Cloud Run fallback

**Project Type**: Local deployment CLI plus containerized web/agent service

**Performance Goals**: Context preparation completes in seconds and copies only the small explicit source allowlist

**Constraints**: No cloud/model calls during tests; no secrets in arguments beyond Secret Manager references; no application behavior changes; one instance and one worker

**Scale/Scope**: One deployment command, two targets, one OpenRouter Secret Manager reference

## Constitution Check

*GATE: Passed before and after design.*

- Local usability remains unchanged; deployment tests and preview need no cloud credentials.
- The model still exposes proposal/read tools only; deployment does not add a confirmation tool.
- JSON remains the only runtime store and is explicitly documented as ephemeral in cloud targets.
- Dependencies remain pinned and the existing A2A/runtime application is reused.
- No deployed/live result is claimed; tests validate packaging and command construction only.
- The context allowlist excludes secrets, runtime records, artifacts, and local tooling.
- Deployment code stays under `deployment/gcp/` and does not alter domain, storage, or transport behavior.

## Project Structure

### Documentation (this feature)

```text
specs/002-python-gcp-deploy/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/deploy-cli.md
`-- tasks.md
```

### Source Code (repository root)

```text
deployment/gcp/
|-- deploy.py
|-- Dockerfile
|-- agents-cli-manifest.yaml
|-- .gcloudignore
`-- README.md

tests/
`-- test_gcp_deploy.py
```

**Structure Decision**: Keep deployment-specific code and container metadata in the existing `deployment/gcp/` boundary. The Python CLI copies only the root lock/project files and application packages into a temporary directory, overlays the deployment Dockerfile and manifest there, calls the pinned Agents CLI from that directory, and always removes the temporary context.

## Complexity Tracking

No constitution violation or additional abstraction is required.
