# Quickstart validation

These checks do not require GCP credentials and do not deploy anything.

```powershell
uv run --no-sync python deployment/gcp/deploy.py agent-runtime `
  --project example-project `
  --service-account booking-agent@example-project.iam.gserviceaccount.com `
  --preview

uv run --no-sync python deployment/gcp/deploy.py cloud-run `
  --project example-project `
  --service-account booking-agent@example-project.iam.gserviceaccount.com `
  --preview

uv run --no-sync python -m pytest -q tests/test_gcp_deploy.py
```

Expected preview output lists only the allowlisted context files and a command containing an `openrouter-api-key:latest` reference. It must not include `.env`, `runtime/`, `artifacts/`, `.git/`, or any API-key value.

An actual deployment is the same command without `--preview`, after completing the credential, API, IAM, and Secret Manager prerequisites in `deployment/gcp/README.md`. No actual deployment is part of local validation.
