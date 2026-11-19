# Feature Specification: Runnable Python GCP Deployment

**Feature Branch**: `002-python-gcp-deploy`

**Created**: 2026-11-19

**Status**: Draft

**Input**: User description: "Replace the demonstration scaffold with actual Python deployment code that can be run later."

## User Scenarios & Testing

### User Story 1 - Deploy from Python (Priority: P1)

As an operator with Google Cloud credentials, I can run one Python command to deploy the existing booking agent to a selected supported Google Cloud target.

**Why this priority**: A runnable deployment command is the requested outcome; documentation or configuration alone is insufficient.

**Independent Test**: Build the deployment command and isolated upload context locally, then verify the command, target, configuration, and packaged files without contacting Google Cloud.

**Acceptance Scenarios**:

1. **Given** a configured GCP project, service account, and Secret Manager secret, **when** the operator selects Agent Runtime, **then** the command performs an Agent Runtime deployment through the pinned Agents CLI.
2. **Given** the same prerequisites, **when** the operator selects Cloud Run, **then** the command performs a private Cloud Run deployment through the pinned Agents CLI.
3. **Given** no credentials, **when** the operator requests command preview, **then** the exact redacted deployment command and build-context contents are available without a cloud request.

---

### User Story 2 - Keep secrets and local data out of uploads (Priority: P2)

As an operator, I can deploy without copying local credentials, runtime JSON, or unrelated workspace files into the cloud build context.

**Why this priority**: Deployment convenience must not weaken the repository's privacy boundary.

**Independent Test**: Seed representative forbidden files outside the allowlist and verify they never appear in the generated build context or rendered command.

**Acceptance Scenarios**:

1. **Given** a local `.env` and runtime files, **when** the deployment context is prepared, **then** neither is copied.
2. **Given** a provider secret name and version, **when** the command is rendered, **then** it contains only the Secret Manager reference and never the secret value.

### Edge Cases

- Required repository files or the Agents CLI executable are missing.
- The target, project ID, region, service account, secret name, or service name is malformed.
- The generated context escapes its temporary directory or contains an unexpected path.
- The deployment command fails after the temporary context is created.
- OpenRouter egress works on Cloud Run but is unsupported or blocked on Agent Runtime.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST provide a directly executable Python deployment command.
- **FR-002**: The command MUST support both Agent Runtime and private Cloud Run targets.
- **FR-003**: The command MUST invoke the repository-pinned Agents CLI rather than an unpinned external deployment implementation.
- **FR-004**: The command MUST pass model, JSON data directory, timezone, resource, port, resource limits, and single-instance constraints explicitly.
- **FR-005**: Provider credentials MUST be supplied only as a Secret Manager name and version reference.
- **FR-006**: The uploaded source context MUST be generated from an explicit allowlist and MUST exclude `.env`, runtime JSON, artifacts, Git metadata, and local agent tooling.
- **FR-007**: The command MUST provide a local preview mode that performs no cloud or model API call.
- **FR-008**: Failures MUST return a nonzero exit status and preserve a useful error message without printing secret values.
- **FR-009**: Existing booking behavior, tools, storage defaults, confirmation rules, A2A behavior, and offline CI MUST remain unchanged.
- **FR-010**: Documentation MUST state that the deployment code is locally validated but not deployed to GCP.
- **FR-011**: Focused tests MUST verify command construction, target selection, context isolation, secret references, and subprocess failure propagation without live cloud calls.

## Success Criteria

### Measurable Outcomes

- **SC-001**: An operator can generate a complete deployment command for either target with one Python invocation.
- **SC-002**: Automated inspection finds zero local secret values and zero non-allowlisted workspace files in the generated context.
- **SC-003**: All focused deployment tests and existing offline checks pass without GCP credentials.
- **SC-004**: Invalid input or a failed deployment process produces a nonzero result before any success claim is made.

## Assumptions

- The future operator has a billed GCP project, Google Cloud authentication, required IAM roles, enabled APIs, and an existing Secret Manager secret.
- `google-agents-cli==1.15.0` remains pinned by the repository lock file for this implementation.
- Agent Runtime is preferred; Cloud Run is the fallback if the external OpenRouter/NVIDIA path is unsupported there.
- The JSON filesystem remains ephemeral and single-instance in both cloud targets; production durability is out of scope.
- No deployment is executed while implementing or testing this feature.
