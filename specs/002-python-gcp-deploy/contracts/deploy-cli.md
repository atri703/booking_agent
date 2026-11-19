# Contract: Python deployment CLI

## Invocation

```text
uv run --no-sync python deployment/gcp/deploy.py TARGET \
  --project PROJECT_ID \
  --service-account SERVICE_ACCOUNT [OPTIONS]
```

`TARGET` is `agent-runtime` or `cloud-run`.

## Required arguments

- `--project`: GCP project ID.
- `--service-account`: runtime service-account email.

## Optional arguments

- `--region`: defaults to `us-central1`.
- `--service-name`: defaults to `booking-agent-openrouter-demo`.
- `--secret-name`: defaults to `openrouter-api-key`.
- `--secret-version`: defaults to `latest`.
- `--model`: defaults to the documented OpenRouter NVIDIA model.
- `--preview`: creates and validates the context, prints the command and file manifest, and performs no subprocess/cloud call.
- `--agents-cli`: optional executable override for advanced environments and tests.

## Exit behavior

- `0`: preview completed or Agents CLI deployment completed successfully.
- `2`: invalid command-line input.
- Nonzero child status: deployment failed; the status propagates.

The command never accepts a provider key value. It accepts only a Secret Manager name/version and passes `OPENROUTER_API_KEY=NAME:VERSION` to Agents CLI.
