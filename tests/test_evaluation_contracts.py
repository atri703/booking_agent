import json
from pathlib import Path

from a2a.types import AgentCard
from google.adk.evaluation.eval_config import EvalConfig
from google.adk.evaluation.eval_set import EvalSet
from google.agents.cli._project import read_project_config
from google.protobuf.json_format import ParseDict

ROOT = Path(__file__).resolve().parents[1]


def test_adk_eval_schemas_and_case_coverage():
    root = ROOT / "tests/eval"
    dataset = EvalSet.model_validate_json((root / "adk/booking.evalset.json").read_text())
    scenarios = json.loads((root / "scenarios.json").read_text())
    assert len(dataset.eval_cases) >= 30
    assert {c.eval_id for c in dataset.eval_cases} == {s["id"] for s in scenarios}
    assert sum(len(c.conversation) > 1 for c in dataset.eval_cases) >= 5
    for filename in ["test_config.json", "judge_config.json"]:
        EvalConfig.model_validate_json((root / "adk" / filename).read_text())


def test_agents_cli_manifest_and_dataset():
    config = read_project_config(str(ROOT))
    assert config.agent_directory == "eval_agent"
    assert config.framework == "google-adk"
    # Use the actual installed Google evaluation SDK schema, not a local imitation.
    from vertexai._genai.types import EvaluationDataset

    raw = json.loads((ROOT / "tests/eval/datasets/booking.json").read_text())
    dataset = EvaluationDataset.model_validate(raw)
    assert len(dataset.eval_cases) >= 30


def test_committed_agent_card_schema():
    card = ParseDict(json.loads((ROOT / "agent-card.json").read_text()), AgentCard())
    assert card.name == "booking_agent"
    assert card.supported_interfaces[0].protocol_version == "1.0"
