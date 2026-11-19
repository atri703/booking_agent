# Tasks: Runnable Python GCP Deployment

**Input**: Design documents from `specs/002-python-gcp-deploy/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

## Phase 1: Setup

- [x] T001 Remove obsolete PowerShell/ADK deployment scaffold files from `deployment/gcp/`
- [x] T002 Add deployment-owned container and Agents CLI metadata in `deployment/gcp/Dockerfile`, `deployment/gcp/agents-cli-manifest.yaml`, and `deployment/gcp/.gcloudignore`

## Phase 2: Foundational tests

- [x] T003 [P] Add failing target/command contract tests in `tests/test_gcp_deploy.py`
- [x] T004 [P] Add failing allowlisted-context and cleanup tests in `tests/test_gcp_deploy.py`
- [x] T005 [P] Add failing subprocess exit propagation and preview isolation tests in `tests/test_gcp_deploy.py`

## Phase 3: User Story 1 - Deploy from Python (Priority: P1)

**Goal**: Provide a real Python command for Agent Runtime and private Cloud Run deployment.

**Independent Test**: Preview both targets and assert the complete pinned Agents CLI commands without credentials.

- [x] T006 [US1] Implement validated `DeploymentConfig` and CLI argument parsing in `deployment/gcp/deploy.py` per `data-model.md`
- [x] T007 [US1] Implement Agents CLI command construction and real subprocess execution in `deployment/gcp/deploy.py` per `contracts/deploy-cli.md`
- [x] T008 [US1] Implement local `--preview` output and nonzero failure propagation in `deployment/gcp/deploy.py`

## Phase 4: User Story 2 - Isolate secrets and local data (Priority: P2)

**Goal**: Generate a temporary source context containing only explicitly approved deployment inputs.

**Independent Test**: Populate forbidden workspace files, prepare a context, and assert they are absent while required application files are present.

- [x] T009 [US2] Implement allowlisted context creation and unconditional cleanup in `deployment/gcp/deploy.py`
- [x] T010 [US2] Pass only Secret Manager references and non-secret runtime settings from `deployment/gcp/deploy.py`

## Phase 5: Polish and validation

- [x] T011 [P] Replace scaffold language and document real Python commands and unverified GCP status in `deployment/gcp/README.md` and `README.md`
- [x] T012 [P] Record current official compatibility sources in `docs/SOURCES.md`
- [x] T013 Remove obsolete wrapper package files under `deployment/gcp/agent_engine/`
- [x] T014 Run focused deployment tests, Ruff, format checks, and relevant existing offline tests
- [x] T015 Validate the implementation against `specs/002-python-gcp-deploy/quickstart.md`

## Dependencies and execution order

- Phase 1 establishes the target file layout.
- Phase 2 tests are written before the Python implementation.
- User Story 1 provides the deploy command and is the MVP.
- User Story 2 builds on the command with upload isolation and secret handling.
- Documentation and validation follow both stories.

## Parallel opportunities

- T003–T005 describe independent test concerns but share one test file, so apply them sequentially in one TDD pass.
- T011 and T012 can proceed independently after command flags stabilize.

## Implementation strategy

Deliver User Story 1 first with previewable commands, then add the strict build-context security boundary, remove the old wrappers, and run offline validation. No command may contact GCP during implementation.
