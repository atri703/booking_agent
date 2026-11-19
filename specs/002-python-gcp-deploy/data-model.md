# Data Model: Deployment Configuration

No booking-domain entity changes are introduced.

## DeploymentConfig

- `target`: `agent_runtime` or `cloud_run`; required.
- `project`: non-empty GCP project ID; required.
- `region`: non-empty GCP region; defaults to `us-central1`.
- `service_account`: service-account email; required.
- `service_name`: lowercase Google Cloud resource name; defaults to `booking-agent-openrouter-demo`.
- `secret_name`: Secret Manager secret resource short name; defaults to `openrouter-api-key`.
- `secret_version`: Secret Manager version; defaults to `latest`.
- `model`: LiteLLM identifier; defaults to `openrouter/nvidia/nemotron-3-ultra-550b-a55b:free`.
- `preview`: when true, prepare and inspect locally without executing Agents CLI.

## PreparedContext

- `root`: unique temporary directory inside the operating-system temporary directory.
- `files`: sorted relative paths copied from the explicit allowlist.
- `command`: argument-vector form of the Agents CLI command; contains secret references but no secret values.

The context exists only for the deployment process and is deleted on success or failure.
