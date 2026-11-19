import pytest

from booking_agent.agent import build_agent
from booking_agent.config import Settings
from booking_agent.service import BookingService
from booking_agent.storage.json_store import JsonStore
from scripts.run_adk_eval import require_live_model_credentials

OPENROUTER_MODEL = "openrouter/nvidia/nemotron-3-ultra-550b-a55b:free"


def test_openrouter_model_selection_reaches_litellm(tmp_path, monkeypatch):
    monkeypatch.setenv("BOOKING_MODEL", OPENROUTER_MODEL)
    settings = Settings.from_env()
    service = BookingService(JsonStore(tmp_path / "bookings.json"), settings)

    agent = build_agent(service=service, settings=settings)

    assert settings.model == OPENROUTER_MODEL
    assert agent.model.model == OPENROUTER_MODEL


@pytest.mark.parametrize(
    ("model", "required_key", "other_key"),
    [
        ("openai/gpt-5.2", "OPENAI_API_KEY", "OPENROUTER_API_KEY"),
        (OPENROUTER_MODEL, "OPENROUTER_API_KEY", "OPENAI_API_KEY"),
    ],
)
def test_live_eval_requires_selected_provider_key(monkeypatch, model, required_key, other_key):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    settings = Settings(model=model)

    with pytest.raises(SystemExit, match=required_key):
        require_live_model_credentials(settings)

    monkeypatch.setenv(other_key, "test-placeholder")
    with pytest.raises(SystemExit, match=required_key):
        require_live_model_credentials(settings)

    monkeypatch.setenv(required_key, "test-placeholder")
    require_live_model_credentials(settings)
