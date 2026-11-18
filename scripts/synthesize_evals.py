"""Generate and grade new conversations with the real Google Agents CLI."""

import argparse
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from dotenv import load_dotenv


def main():
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--max-turns", type=int, default=8)
    parser.add_argument("--grade", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.count <= 50 or not 1 <= args.max_turns <= 12:
        parser.error("Use count 1–50 and max-turns 1–12")
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("Set OPENAI_API_KEY for the agent under test")
    if not os.getenv("GOOGLE_CLOUD_PROJECT"):
        raise SystemExit("Set GOOGLE_CLOUD_PROJECT and authenticate Google ADC for synthesis")
    executable = shutil.which("agents-cli")
    if not executable:
        raise SystemExit("Install tools: uv sync --all-extras")
    root = Path(__file__).resolve().parents[1]
    output = root / "artifacts/synthetic-traces.json"
    output.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="booking-synthetic-") as directory:
        env = os.environ | {"BOOKING_EVAL_DIR": directory}
        subprocess.run(
            [
                executable,
                "eval",
                "dataset",
                "synthesize",
                "--count",
                str(args.count),
                "--max-turns",
                str(args.max_turns),
                "--output",
                str(output),
                "--instruction",
                "Test appointment availability, missing details, changes of mind, "
                "invalid dates, prompt injection and proposal creation. "
                "Final goal is a valid proposal "
                "and client confirmation instructions, not a committed booking.",
                "--environment-context",
                "Today is 2030-01-07. Business timezone Asia/Kolkata. "
                "Advisor works weekdays 09:00–17:00. Durations 30/60 minutes. "
                "Empty isolated store. "
                "Actual commits require REST human confirmation unavailable to the simulator.",
            ],
            cwd=root,
            env=env,
            check=True,
        )
    if args.grade:
        subprocess.run(
            [
                executable,
                "eval",
                "grade",
                "--traces",
                str(output),
                "--config",
                "tests/eval/eval_config.yaml",
            ],
            cwd=root,
            check=True,
        )


if __name__ == "__main__":
    main()
