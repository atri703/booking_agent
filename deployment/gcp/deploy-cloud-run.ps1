[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,

    [string]$Region = "us-central1",

    [Parameter(Mandatory = $true)]
    [string]$ServiceAccount,

    [string]$ServiceName = "booking-agent-openrouter-demo",

    [string]$SecretName = "openrouter-api-key"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$agentDir = Join-Path $repoRoot "deployment\gcp\agent_engine\booking_agent_gcp"
$stageDir = Join-Path ([IO.Path]::GetTempPath()) ("booking-agent-cloud-run-" + [guid]::NewGuid())
$pushedLocation = $false

New-Item -ItemType Directory -Path $stageDir | Out-Null

try {
    Push-Location $repoRoot
    $pushedLocation = $true

    uv build --wheel --out-dir $stageDir
    if ($LASTEXITCODE -ne 0) {
        throw "Building the deployment wheel failed."
    }

    $wheels = @(Get-ChildItem -LiteralPath $stageDir -Filter "*.whl")
    if ($wheels.Count -ne 1) {
        throw "Expected exactly one deployment wheel, found $($wheels.Count)."
    }
    $wheel = $wheels[0]

    uv run --no-sync adk deploy cloud_run `
        "--project=$ProjectId" `
        "--region=$Region" `
        "--service_name=$ServiceName" `
        "--python_version=3.12" `
        "--extra_packages=$($wheel.FullName)" `
        --a2a `
        --env "BOOKING_MODEL=openrouter/nvidia/nemotron-3-ultra-550b-a55b:free" `
        --env "BOOKING_DATA_DIR=/tmp/booking-agent" `
        --env "BOOKING_TIMEZONE=Asia/Kolkata" `
        --env "BOOKING_RESOURCE=advisor" `
        $agentDir `
        -- `
        --no-allow-unauthenticated `
        "--service-account=$ServiceAccount" `
        "--set-secrets=OPENROUTER_API_KEY=$SecretName`:latest" `
        --min-instances=0 `
        --max-instances=1

    if ($LASTEXITCODE -ne 0) {
        throw "Cloud Run deployment failed."
    }
}
finally {
    if ($pushedLocation) {
        Pop-Location
    }

    $resolvedTemp = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
    $resolvedStage = [IO.Path]::GetFullPath($stageDir)
    if ($resolvedStage.StartsWith($resolvedTemp, [StringComparison]::OrdinalIgnoreCase)) {
        Remove-Item -LiteralPath $resolvedStage -Recurse -Force -ErrorAction SilentlyContinue
    }
}
