"""Deploy the existing booking service through the pinned Google Agents CLI.

The deployment context is assembled from an allowlist so local credentials, runtime
JSON, traces, Git metadata, and unrelated workspace files cannot be uploaded.
"""

from __future__ import annotations

import argparse
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEPLOYMENT_ROOT = Path(__file__).resolve().parent
DEFAULT_MODEL = "openrouter/nvidia/nemotron-3-ultra-550b-a55b:free"

_PROJECT_ID = re.compile(r"^[a-z][a-z0-9-]{4,28}[a-z0-9]$")
_REGION = re.compile(r"^[a-z][a-z0-9-]{0,30}[a-z0-9]$")
_SERVICE_ACCOUNT = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._-]*@"
    r"[a-z][a-z0-9-]{4,28}[a-z0-9]\.iam\.gserviceaccount\.com$"
)
_RESOURCE_NAME = re.compile(r"^[a-z](?:[a-z0-9-]{0,61}[a-z0-9])?$")
_SECRET_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,254}$")
_SECRET_VERSION = re.compile(r"^(?:latest|[1-9][0-9]*|[A-Za-z][A-Za-z0-9_-]{0,62})$")

_SOURCE_FILES = ("pyproject.toml", "uv.lock")
_SOURCE_PACKAGES = ("booking_agent", "coordinator", "eval_agent")
_SOURCE_SUFFIXES = {".py", ".html"}
_DEPLOYMENT_ASSETS = {
    "Dockerfile": "Dockerfile",
    "agents-cli-manifest.yaml": "agents-cli-manifest.yaml",
    ".gcloudignore": ".gcloudignore",
    "README.md": "README.md",
}


@dataclass(frozen=True)
class DeploymentConfig:
    target: str
    project: str
    region: str
    service_account: str
    service_name: str
    secret_name: str
    secret_version: str
    model: str = DEFAULT_MODEL

    def __post_init__(self) -> None:
        checks = (
            ("target", self.target in {"agent_runtime", "cloud_run"}),
            ("project", bool(_PROJECT_ID.fullmatch(self.project))),
            ("region", bool(_REGION.fullmatch(self.region))),
            ("service account", bool(_SERVICE_ACCOUNT.fullmatch(self.service_account))),
            ("service name", bool(_RESOURCE_NAME.fullmatch(self.service_name))),
            ("secret name", bool(_SECRET_NAME.fullmatch(self.secret_name))),
            ("secret version", bool(_SECRET_VERSION.fullmatch(self.secret_version))),
            ("model", bool(self.model) and not any(c in self.model for c in ",=\r\n")),
        )
        for label, valid in checks:
            if not valid:
                raise ValueError(f"Invalid {label}")

    @property
    def secret_reference(self) -> str:
        return f"{self.secret_name}:{self.secret_version}"


@dataclass(frozen=True)
class PreparedContext:
    root: Path
    files: tuple[str, ...]


def _copy_file(source: Path, destination: Path) -> None:
    if source.is_symlink():
        raise ValueError(f"Deployment input may not be a symlink: {source}")
    if not source.is_file():
        raise FileNotFoundError(f"Required deployment input is missing: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


@contextmanager
def prepared_context(repo_root: Path = REPOSITORY_ROOT) -> Iterator[PreparedContext]:
    """Yield a disposable, allowlisted Agents CLI build context."""
    repo_root = repo_root.resolve()
    with tempfile.TemporaryDirectory(prefix="booking-agent-gcp-") as directory:
        context_root = Path(directory)

        for relative in _SOURCE_FILES:
            _copy_file(repo_root / relative, context_root / relative)

        for package in _SOURCE_PACKAGES:
            source_package = repo_root / package
            if not source_package.is_dir() or source_package.is_symlink():
                raise FileNotFoundError(f"Required source package is missing: {source_package}")
            for source in source_package.rglob("*"):
                if source.is_file() and source.suffix in _SOURCE_SUFFIXES:
                    relative = source.relative_to(repo_root)
                    _copy_file(source, context_root / relative)

        for source_name, destination_name in _DEPLOYMENT_ASSETS.items():
            _copy_file(DEPLOYMENT_ROOT / source_name, context_root / destination_name)

        files = tuple(
            sorted(
                path.relative_to(context_root).as_posix()
                for path in context_root.rglob("*")
                if path.is_file()
            )
        )
        yield PreparedContext(root=context_root, files=files)


def build_command(config: DeploymentConfig, executable: Sequence[str] | None = None) -> list[str]:
    """Build the pinned Agents CLI invocation without executing it."""
    command = list(executable or (sys.executable, "-m", "google.agents.cli.main"))
    env_vars = ",".join(
        (
            f"BOOKING_MODEL={config.model}",
            "BOOKING_DATA_DIR=/tmp/booking-agent",
            "BOOKING_TIMEZONE=Asia/Kolkata",
            "BOOKING_RESOURCE=advisor",
            "BOOKING_A2A_URL=http://127.0.0.1:8080",
        )
    )
    command.extend(
        (
            "deploy",
            "--project",
            config.project,
            "--region",
            config.region,
            "--deployment-target",
            config.target,
            "--service-account",
            config.service_account,
            "--service-name",
            config.service_name,
            "--no-agent-identity",
            "--secrets",
            f"OPENROUTER_API_KEY={config.secret_reference}",
            "--env-vars",
            env_vars,
            "--port",
            "8080",
            "--memory",
            "2Gi",
            "--cpu",
            "1",
            "--min-instances",
            "0",
            "--max-instances",
            "1",
            "--concurrency",
            "1",
            "--labels",
            "application=booking-agent,storage=ephemeral-json",
            "--no-confirm-project",
        )
    )
    if config.target == "agent_runtime":
        command.extend(("--framework", "google-adk"))
    else:
        command.extend(("--timeout", "120", "--ingress", "all"))
    return command


def deploy(
    config: DeploymentConfig,
    *,
    repo_root: Path = REPOSITORY_ROOT,
    preview: bool = False,
    executable: Sequence[str] | None = None,
    runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
) -> int:
    """Prepare the safe context and either preview or execute the deployment."""
    with prepared_context(repo_root) as context:
        command = build_command(config, executable=executable)
        print("Deployment context files:")
        for relative in context.files:
            print(f"  {relative}")
        print("Command:")
        print(f"  {shlex.join(command)}")
        if preview:
            print("PREVIEW ONLY: Agents CLI was not executed.")
            return 0
        completed = runner(command, cwd=context.root, check=False)
        return completed.returncode


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Deploy the booking agent with the pinned Google Agents CLI."
    )
    parser.add_argument("target", choices=("agent-runtime", "cloud-run"))
    parser.add_argument("--project", required=True)
    parser.add_argument("--region", default="us-central1")
    parser.add_argument("--service-account", required=True)
    parser.add_argument("--service-name", default="booking-agent-openrouter-demo")
    parser.add_argument("--secret-name", default="openrouter-api-key")
    parser.add_argument("--secret-version", default="latest")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Print the context and command without executing Agents CLI.",
    )
    parser.add_argument(
        "--agents-cli",
        help="Optional Agents CLI path; defaults to the current Python environment.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        config = DeploymentConfig(
            target=args.target.replace("-", "_"),
            project=args.project,
            region=args.region,
            service_account=args.service_account,
            service_name=args.service_name,
            secret_name=args.secret_name,
            secret_version=args.secret_version,
            model=args.model,
        )
        executable = [args.agents_cli] if args.agents_cli else None
        return deploy(config, preview=args.preview, executable=executable)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Deployment configuration error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"Could not execute Agents CLI: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
