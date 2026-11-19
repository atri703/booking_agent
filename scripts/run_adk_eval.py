"""Run ADK Eval per case with an isolated store and assert final domain state.

--offline validates the eval engine with a scripted model, not GPT-5.2 quality.
--judge uses Google-backed rubric judging in addition to final-state checks.
"""

import argparse
import asyncio
import json
import os
import tempfile
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from google.adk.evaluation.agent_evaluator import AgentEvaluator

from booking_agent.agent import build_agent
from booking_agent.config import Settings, model_api_key_name
from booking_agent.models import Booking
from booking_agent.service import BookingService
from booking_agent.storage.json_store import JsonStore

ROOT = Path(__file__).resolve().parents[1]
FIXED_NOW = datetime(2030, 1, 7, tzinfo=UTC)


def require_live_model_credentials(settings: Settings) -> None:
    api_key_name = model_api_key_name(settings.model)
    if not os.getenv(api_key_name):
        raise SystemExit(f"{api_key_name} is required for live ADK evaluation")


async def evaluate(offline=False, judge=False, case_id=None):
    base_settings = Settings.from_env()
    if not offline:
        require_live_model_credentials(base_settings)
    scenarios = json.loads((ROOT / "tests/eval/scenarios.json").read_text())
    dataset = json.loads((ROOT / "tests/eval/adk/booking.evalset.json").read_text())
    cases = {case["eval_id"]: case for case in dataset["eval_cases"]}
    if offline:
        scenarios = [dict(id="offline_policy", expected_proposals=0, seed=False)]
        cases = {
            "offline_policy": {
                "eval_id": "offline_policy",
                "conversation": [
                    {
                        "user_content": {
                            "role": "user",
                            "parts": [{"text": "What is your booking policy?"}],
                        },
                        "intermediate_data": {
                            "tool_uses": [{"name": "booking_policy", "args": {}}]
                        },
                        "final_response": {
                            "role": "model",
                            "parts": [
                                {"text": "Please review the proposal and confirm using the client."}
                            ],
                        },
                    }
                ],
            }
        }
    if case_id:
        scenarios = [s for s in scenarios if s["id"] == case_id]
        if not scenarios:
            raise SystemExit(f"Unknown case: {case_id}")
    results = []
    for scenario in scenarios:
        with tempfile.TemporaryDirectory(prefix="booking-eval-") as directory:
            path = Path(directory)
            settings = replace(base_settings, data_dir=path)
            store = JsonStore(path / "bookings.json")
            service = BookingService(store, settings, clock=lambda: FIXED_NOW)
            if scenario["seed"]:
                b = Booking(
                    id="existing-booking",
                    owner="demo-user",
                    customer_name="Atri",
                    start="2030-01-08T10:00:00+05:30",
                )
                store.transact(
                    lambda state, b=b: state["bookings"].update({b.id: b.model_dump(mode="json")})
                )
            before = store.read()["bookings"]
            model = None
            if offline:
                from tests.fake_model import ScriptedModel

                model = ScriptedModel()
            agent = build_agent(service, settings, model=model)
            config_name = "judge_config.json" if judge else "test_config.json"
            config = json.loads((ROOT / "tests/eval/adk" / config_name).read_text())
            if judge and not offline:
                config["criteria"]["rubric_based_final_response_quality_v1"]["rubrics"].append(
                    {
                        "rubric_id": "case_expected_behavior",
                        "rubric_content": {"text_property": scenario["rubric"]},
                    }
                )
            # Negative/clarification cases have no prescribed tool path. Their
            # acceptance is final-state checks; quality requires --judge.
            if not judge and not any(
                t.get("intermediate_data", {}).get("tool_uses")
                for t in cases[scenario["id"]]["conversation"]
            ):
                config["criteria"] = {}
            (path / "test_config.json").write_text(json.dumps(config))
            evalfile = path / "case.evalset.json"
            evalfile.write_text(
                json.dumps({"eval_set_id": scenario["id"], "eval_cases": [cases[scenario["id"]]]})
            )
            try:
                await AgentEvaluator.evaluate(
                    agent,
                    str(evalfile),
                    num_runs=1,
                    app_name="booking_agent",
                    parallelism=1,
                    print_detailed_results=False,
                )
                assert store.read()["bookings"] == before, (
                    "Agent mutated bookings without client confirmation"
                )
                assert len(store.read()["proposals"]) == scenario["expected_proposals"], (
                    "Unexpected proposal count"
                )
                results.append({"case": scenario["id"], "passed": True})
            except Exception as exc:
                results.append(
                    {
                        "case": scenario["id"],
                        "passed": False,
                        "error": type(exc).__name__,
                        "detail": str(exc)[:1000],
                    }
                )
    out = ROOT / "artifacts"
    out.mkdir(exist_ok=True)
    report = out / ("adk-offline.json" if offline else "adk-live.json")
    report.write_text(
        json.dumps(
            {
                "mode": "offline-scripted" if offline else base_settings.model,
                "judge": judge,
                "results": results,
            },
            indent=2,
        )
        + "\n"
    )
    print(f"{sum(r['passed'] for r in results)}/{len(results)} cases passed; report: {report}")
    if not all(r["passed"] for r in results):
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--judge", action="store_true")
    parser.add_argument("--case")
    args = parser.parse_args()
    asyncio.run(evaluate(args.offline, args.judge, args.case))


if __name__ == "__main__":
    main()
