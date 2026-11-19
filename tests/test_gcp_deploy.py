import subprocess
from pathlib import Path

import pytest
from google.agents.cli._project import read_project_config

from deployment.gcp.deploy import (
    DeploymentConfig,
    build_command,
    deploy,
    prepared_context,
)


def config(target="agent_runtime"):
    return DeploymentConfig(
        target=target,
        project="example-project",
        region="us-central1",
        service_account="booking-agent@example-project.iam.gserviceaccount.com",
        service_name="booking-agent-openrouter-demo",
        secret_name="openrouter-api-key",
        secret_version="latest",
        model="openrouter/nvidia/nemotron-3-ultra-550b-a55b:free",
    )


def option(command, name):
    return command[command.index(name) + 1]


def test_agent_runtime_command_uses_pinned_cli_contract():
    command = build_command(config(), executable=["python", "-m", "google.agents.cli.main"])

    assert command[:4] == ["python", "-m", "google.agents.cli.main", "deploy"]
    assert option(command, "--deployment-target") == "agent_runtime"
    assert option(command, "--project") == "example-project"
    assert option(command, "--service-account").endswith(".iam.gserviceaccount.com")
    assert option(command, "--secrets") == "OPENROUTER_API_KEY=openrouter-api-key:latest"
    assert "BOOKING_MODEL=openrouter/nvidia/nemotron-3-ultra-550b-a55b:free" in option(
        command, "--env-vars"
    )
    assert option(command, "--max-instances") == "1"
    assert option(command, "--concurrency") == "1"
    assert option(command, "--framework") == "google-adk"
    assert "--no-agent-identity" in command


def test_cloud_run_command_is_private_and_has_timeout():
    command = build_command(config("cloud_run"), executable=["agents-cli"])

    assert option(command, "--deployment-target") == "cloud_run"
    assert option(command, "--timeout") == "120"
    assert option(command, "--ingress") == "all"
    assert "--framework" not in command
    assert "--allow-unauthenticated" not in command


def test_config_rejects_values_that_can_break_cli_serialization():
    with pytest.raises(ValueError, match="model"):
        DeploymentConfig(
            target="agent_runtime",
            project="example-project",
            region="us-central1",
            service_account="booking-agent@example-project.iam.gserviceaccount.com",
            service_name="booking-agent",
            secret_name="openrouter-api-key",
            secret_version="latest",
            model="openrouter/model,INJECTED=value",
        )


def make_repository(path: Path):
    (path / "pyproject.toml").write_text("[project]\nname='test'\n")
    (path / "uv.lock").write_text("version = 1\n")
    (path / ".env").write_text("OPENROUTER_API_KEY=must-not-copy\n")
    (path / "runtime").mkdir()
    (path / "runtime" / "bookings.json").write_text('{"private": true}\n')
    (path / "artifacts").mkdir()
    (path / "artifacts" / "trace.json").write_text("{}\n")
    for package in ("booking_agent", "coordinator", "eval_agent"):
        package_dir = path / package
        package_dir.mkdir()
        (package_dir / "__init__.py").write_text("")
        (package_dir / "module.py").write_text("VALUE = 1\n")
        (package_dir / ".env").write_text("SECRET=must-not-copy\n")
        (package_dir / "cache.json").write_text("{}\n")
    (path / "booking_agent" / "index.html").write_text("<h1>booking</h1>\n")


def test_prepared_context_copies_only_allowlisted_inputs(tmp_path):
    make_repository(tmp_path)

    with prepared_context(tmp_path) as context:
        context_path = context.root
        files = context.files
        assert "pyproject.toml" in files
        assert "uv.lock" in files
        assert "booking_agent/module.py" in files
        assert "booking_agent/index.html" in files
        assert "Dockerfile" in files
        assert "agents-cli-manifest.yaml" in files
        assert not any(".env" in item for item in files)
        assert not any(item.startswith("runtime/") for item in files)
        assert not any(item.startswith("artifacts/") for item in files)
        assert not any(item.endswith("cache.json") for item in files)
        manifest = read_project_config(str(context.root))
        assert manifest.agent_directory == "booking_agent"
        assert manifest.deployment_target == "agent_runtime"
        assert manifest.is_a2a is True

    assert not context_path.exists()


def test_preview_never_runs_a_subprocess(tmp_path, capsys):
    make_repository(tmp_path)

    def unexpected_runner(*args, **kwargs):
        raise AssertionError("preview must not execute Agents CLI")

    result = deploy(config(), repo_root=tmp_path, preview=True, runner=unexpected_runner)

    assert result == 0
    output = capsys.readouterr().out
    assert "PREVIEW ONLY" in output
    assert "openrouter-api-key:latest" in output
    assert "must-not-copy" not in output


def test_deploy_propagates_agents_cli_exit_status(tmp_path):
    make_repository(tmp_path)
    observed = {}

    def failed_runner(command, **kwargs):
        observed["command"] = command
        observed["cwd"] = Path(kwargs["cwd"])
        assert observed["cwd"].exists()
        return subprocess.CompletedProcess(command, 17)

    result = deploy(config(), repo_root=tmp_path, runner=failed_runner)

    assert result == 17
    assert option(observed["command"], "--deployment-target") == "agent_runtime"
    assert not observed["cwd"].exists()
