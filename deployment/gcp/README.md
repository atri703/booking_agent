# Deploy the booking agent to GCP

This folder contains executable Python deployment code, not a placeholder scaffold. The command
creates a clean temporary build context and invokes the repository-pinned Google Agents CLI for
either Gemini Enterprise Agent Runtime or private Cloud Run.

The code and offline preview have been tested locally. No GCP credentials were available, the
real deployment path has not been executed, and nothing from this repository has been deployed
to Google Cloud.

## What gets deployed

`deploy.py` copies only these inputs into a disposable directory:

- `pyproject.toml` and `uv.lock`
- Python/HTML source under `booking_agent/`, `coordinator/`, and `eval_agent/`
- this folder's `Dockerfile`, `agents-cli-manifest.yaml`, `.gcloudignore`, and README

It does not copy `.env`, `runtime/`, `artifacts/`, Git metadata, Graphify output, or other
workspace files. The provider credential is never accepted as a command argument; deployment
passes only a Secret Manager reference to Agents CLI.

Both targets run the existing FastAPI/ADK/A2A application on port 8080 with one worker and one
instance. The model remains unable to confirm bookings. JSON is stored under
`/tmp/booking-agent`, which is ephemeral and not shared or durable.

## Prerequisites for a future real deployment

Use a billed demo project. Install the repository dependencies, Google Cloud CLI, and authenticate
both gcloud and Application Default Credentials:

```powershell
uv sync --locked --all-extras
gcloud auth login
gcloud auth application-default login
gcloud config set project PROJECT_ID
```

Enable the required services:

```powershell
gcloud services enable `
  aiplatform.googleapis.com `
  cloudbuild.googleapis.com `
  run.googleapis.com `
  artifactregistry.googleapis.com `
  secretmanager.googleapis.com
```

Create a dedicated runtime service account and the secret container:

```powershell
gcloud iam service-accounts create booking-agent-demo-runtime `
  --display-name="Booking agent demo runtime"
gcloud secrets create openrouter-api-key --replication-policy=automatic
```

Add the real OpenRouter key as a new secret version through the Secret Manager console. This
avoids placing it in the repository or shell history. Grant the runtime service account access:

```powershell
gcloud secrets add-iam-policy-binding openrouter-api-key `
  --member="serviceAccount:booking-agent-demo-runtime@PROJECT_ID.iam.gserviceaccount.com" `
  --role="roles/secretmanager.secretAccessor"
```

The deploying identity also needs the Agents CLI/Google Cloud roles documented for the selected
target, including permission to act as the runtime service account. Agent Runtime may additionally
require its managed service agent to read injected secrets, depending on the project configuration.

## Safe local preview

Preview prepares and validates the exact context and prints the exact command. It never starts
Agents CLI and needs no GCP credentials:

```powershell
uv run --no-sync python deployment/gcp/deploy.py agent-runtime `
  --project PROJECT_ID `
  --service-account booking-agent-demo-runtime@PROJECT_ID.iam.gserviceaccount.com `
  --preview
```

Preview the Cloud Run fallback by changing the target to `cloud-run`.

## Actual Agent Runtime deployment

After credentials, billing, IAM, APIs, and the secret are ready, remove `--preview`:

```powershell
uv run --no-sync python deployment/gcp/deploy.py agent-runtime `
  --project PROJECT_ID `
  --region us-central1 `
  --service-account booking-agent-demo-runtime@PROJECT_ID.iam.gserviceaccount.com
```

The Python command executes the pinned equivalent of:

```text
agents-cli deploy --deployment-target agent_runtime ...
```

It injects `OPENROUTER_API_KEY=openrouter-api-key:latest` as a Secret Manager reference and
passes all non-secret runtime settings explicitly. Agent Runtime outbound access for this exact
OpenRouter/NVIDIA LiteLLM combination remains unverified; a successful deployment is not proof
until a real inference request succeeds.

## Actual private Cloud Run fallback

If Agent Runtime cannot use the external model, run:

```powershell
uv run --no-sync python deployment/gcp/deploy.py cloud-run `
  --project PROJECT_ID `
  --region us-central1 `
  --service-account booking-agent-demo-runtime@PROJECT_ID.iam.gserviceaccount.com
```

Agents CLI deploys Cloud Run privately by default; callers need Google identity authorization.
The command does not include an unauthenticated-access flag. Do not make this single-user demo
public.

## Options

```text
--service-name NAME       Cloud resource name (default: booking-agent-openrouter-demo)
--secret-name NAME        Secret Manager name (default: openrouter-api-key)
--secret-version VERSION  Secret version or alias (default: latest)
--model MODEL             LiteLLM model identifier
--agents-cli PATH         Override the Agents CLI executable
--preview                 Perform no subprocess or cloud call
```

The default model is:

```text
openrouter/nvidia/nemotron-3-ultra-550b-a55b:free
```

## Local validation

```powershell
uv run --no-sync python -m pytest -q tests/test_gcp_deploy.py
uv run --no-sync ruff check deployment/gcp/deploy.py tests/test_gcp_deploy.py
uv run --no-sync ruff format --check deployment/gcp/deploy.py tests/test_gcp_deploy.py
```

These checks validate arguments, commands, targets, secret references, file allowlisting,
temporary-directory cleanup, preview isolation, and failed-process status propagation. They do
not prove IAM, provider egress, cloud build, or deployed inference.

## Cleanup after a future deployment

Deployments can create billable Agent Runtime, Cloud Build, Artifact Registry, Cloud Run,
logging, and Secret Manager resources. After a demonstration, list deployments with
`agents-cli deploy --list` and delete the runtime/service and unneeded images or secrets using
the Google Cloud console or corresponding Google Cloud commands.

## Official documentation checked

- Agents CLI deployment: https://google.github.io/agents-cli/guide/deployment/
- Agents CLI flags: https://google.github.io/agents-cli/cli/
- Agent Runtime deployment: https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/runtime/deploy-an-agent
- Cloud Run source deployment: https://docs.cloud.google.com/run/docs/deploying-source-code
