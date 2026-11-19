[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId,

    [string]$Region = "us-central1",

    [Parameter(Mandatory = $true)]
    [string]$ServiceAccount,

    [string]$DisplayName = "booking-agent-openrouter-demo"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$agentDir = Join-Path $repoRoot "deployment\gcp\agent_engine\booking_agent_gcp"
$stageDir = Join-Path ([IO.Path]::GetTempPath()) ("booking-agent-engine-" + [guid]::NewGuid())
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

    uv run --no-sync adk deploy agent_engine `
        "--project=$ProjectId" `
        "--region=$Region" `
        "--service_account=$ServiceAccount" `
        "--display_name=$DisplayName" `
        "--python_version=3.12" `
        "--extra_packages=$($wheel.FullName)" `
        $agentDir

    if ($LASTEXITCODE -ne 0) {
        throw "Agent Runtime deployment failed."
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
