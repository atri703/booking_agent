# GCP deployment demonstration

This folder is a deployment **demonstration scaffold only**. The booking agent has been
tested locally, including one live OpenRouter evaluation case, but none of the commands in
this folder have been run against Google Cloud and no code has been deployed to GCP.

The preferred target is Gemini Enterprise Agent Platform Agent Runtime (still named
`agent_engine` in the ADK CLI). A private Cloud Run deployment is included as a fallback if
the external LiteLLM/OpenRouter model cannot be reached or supported in Agent Runtime.

## Important limitations

- This remains the single-user demo described in the repository security documentation.
- Agent Runtime and Cloud Run use `/tmp/booking-agent` for the existing JSON store. That
  filesystem is ephemeral and is not shared across instances. `max_instances=1` reduces
  inconsistency but does not make the data durable.
- The deployed ADK surfaces expose the agent, not the repository's browser UI or trusted REST
  confirmation client. The model can create proposals but cannot commit bookings.
- OpenRouter/NVIDIA through ADK `LiteLlm` has not been validated on either GCP target.
- Do not deploy real customer data or treat this scaffold as production-ready.
- Never copy the repository `.env` into this folder. Both deployment paths use Secret Manager.

## Folder layout

```text
deployment/gcp/
|-- agent_engine/booking_agent_gcp/  # ADK-discoverable wrapper and runtime config
|-- deploy-agent-engine.ps1          # preferred Agent Runtime deployment
`-- deploy-cloud-run.ps1             # private Cloud Run fallback
```

Both scripts build the repository as a wheel in a temporary directory. They do not stage the
repository directory itself, preventing `.env`, `runtime/`, and other local files from being
included in the upload.

## Prerequisites (do not run until GCP credentials are available)

Install and initialize the Google Cloud CLI, select a billed project, and authenticate both
the CLI and Application Default Credentials:

```powershell
gcloud auth login
gcloud auth application-default login
gcloud config set project PROJECT_ID
```

Enable the APIs used by Agent Runtime, Cloud Build, Cloud Run, Artifact Registry, and Secret
Manager:

```powershell
gcloud services enable aiplatform.googleapis.com cloudbuild.googleapis.com run.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com
```

Create a dedicated runtime service account and a Secret Manager secret. Add the existing
OpenRouter key as a secret version through the Secret Manager console so it does not appear in
shell history:

```powershell
gcloud iam service-accounts create booking-agent-demo-runtime --display-name="Booking agent demo runtime"
gcloud secrets create openrouter-api-key --replication-policy=automatic
```

The service-account email will be:

```text
booking-agent-demo-runtime@PROJECT_ID.iam.gserviceaccount.com
```

Grant that runtime identity access to the secret:

```powershell
gcloud secrets add-iam-policy-binding openrouter-api-key --member="serviceAccount:booking-agent-demo-runtime@PROJECT_ID.iam.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"
```

For Agent Runtime secret injection, current Google documentation also requires its managed
service agent to read the secret during deployment:

```powershell
$projectNumber = gcloud projects describe PROJECT_ID --format="value(projectNumber)"
gcloud secrets add-iam-policy-binding openrouter-api-key --member="serviceAccount:service-$projectNumber@gcp-sa-aiplatform.iam.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"
```

The deploying identity also needs the roles listed in the current Google deployment
documentation. Keep permissions project-specific and use a separate demo project where
possible.

## Preferred: Agent Runtime / Agent Engine

From the repository root, after credentials, IAM, billing, APIs, and the secret are ready:

```powershell
.\deployment\gcp\deploy-agent-engine.ps1 `
  -ProjectId PROJECT_ID `
  -Region us-central1 `
  -ServiceAccount booking-agent-demo-runtime@PROJECT_ID.iam.gserviceaccount.com
```

The script runs the pinned equivalent of:

```text
adk deploy agent_engine --project ... --region ... --service_account ... --extra_packages <temporary-wheel> deployment/gcp/agent_engine/booking_agent_gcp
```

The runtime configuration references `openrouter-api-key:latest`; it contains no secret
value. Google documents public outbound calls from Agent Runtime, but does not explicitly
guarantee this repository's OpenRouter/NVIDIA LiteLLM combination. Treat successful model
inference as an integration check that still needs to be performed.

## Fallback: private Cloud Run ADK service

Use this only if Agent Runtime cannot run the external model path:

```powershell
.\deployment\gcp\deploy-cloud-run.ps1 `
  -ProjectId PROJECT_ID `
  -Region us-central1 `
  -ServiceAccount booking-agent-demo-runtime@PROJECT_ID.iam.gserviceaccount.com
```

The script uses `adk deploy cloud_run`, passes the same temporary wheel, injects the key from
Secret Manager, enables A2A, and passes `--no-allow-unauthenticated` to Cloud Run. Invoke the
private service with an authenticated client; do not make this single-user demo public.

## Cleanup after an actual demonstration

The deployment commands may create billable Agent Runtime, Cloud Build, Artifact Registry,
Cloud Run, logging, and Secret Manager resources. After a future test, delete the deployed
runtime or Cloud Run service and any unneeded build images/secrets from the GCP console or the
corresponding `gcloud` commands.

## Official documentation checked

- ADK CLI Agent Engine deployment:
  https://docs.cloud.google.com/iam/docs/create-and-deploy-agent
- Agent Runtime deployment, environment variables, and Secret Manager references:
  https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/runtime/deploy-an-agent
- Agent Runtime external/public endpoint networking:
  https://docs.cloud.google.com/gemini/enterprise/docs/security-overview
- ADK agent deployment on Cloud Run:
  https://docs.cloud.google.com/run/docs/ai/build-and-deploy-ai-agents/deploy-adk-agent
- Cloud Run source deployment and Secret Manager flags:
  https://docs.cloud.google.com/run/docs/deploying-source-code
