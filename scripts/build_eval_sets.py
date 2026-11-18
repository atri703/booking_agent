"""Export reviewed scenarios to ADK and Agents CLI schemas; no LLM generation here."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build():
    scenarios = json.loads((ROOT / "tests/eval/scenarios.json").read_text())
    adk_cases, cli_cases = [], []
    for case in scenarios:
        turns = []
        for i, turn in enumerate(case["turns"]):
            turns.append(
                {
                    "invocation_id": f"{case['id']}-{i}",
                    "user_content": {"role": "user", "parts": [{"text": turn["user"]}]},
                    "final_response": {"role": "model", "parts": [{"text": turn["reference"]}]},
                    "intermediate_data": {"tool_uses": turn.get("tools", [])},
                }
            )
        adk_cases.append(
            {
                "eval_id": case["id"],
                "conversation": turns,
                "session_input": {"app_name": "booking_agent", "user_id": "demo-user", "state": {}},
            }
        )
        cli_cases.append(
            {
                "eval_case_id": case["id"],
                "agent_data": {
                    "agents": {
                        "booking_agent": {"agent_id": "booking_agent", "agent_type": "LlmAgent"}
                    },
                    "turns": [
                        {
                            "turn_index": i,
                            "events": [
                                {
                                    "author": "user",
                                    "content": {"role": "user", "parts": [{"text": t["user"]}]},
                                }
                            ],
                        }
                        for i, t in enumerate(case["turns"])
                    ],
                },
                "expected_behavior": case["rubric"],
            }
        )
    (ROOT / "tests/eval/adk/booking.evalset.json").write_text(
        json.dumps({"eval_set_id": "booking_regression", "eval_cases": adk_cases}, indent=2) + "\n"
    )
    (ROOT / "tests/eval/datasets/booking.json").write_text(
        json.dumps({"eval_cases": cli_cases}, indent=2) + "\n"
    )


if __name__ == "__main__":
    build()
