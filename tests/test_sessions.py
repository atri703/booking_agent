import pytest
from google.adk.events import Event, EventActions
from google.genai import types

from booking_agent.sessions import JsonSessionService


async def test_reconnect_restores_events_and_state(tmp_path):
    path = tmp_path / "sessions.json"
    service = JsonSessionService(path)
    session = await service.create_session(app_name="app", user_id="alice", session_id="s")
    event = Event(
        author="user",
        content=types.Content(role="user", parts=[types.Part(text="hello")]),
        actions=EventActions(state_delta={"pending": "p1", "temp:hidden": 1, "user:name": "Atri"}),
    )
    await service.append_event(session, event)
    other = JsonSessionService(path)
    restored = await other.get_session(app_name="app", user_id="alice", session_id="s")
    assert restored.events[0].content.parts[0].text == "hello"
    assert restored.state["pending"] == "p1"
    assert "temp:hidden" not in restored.state
    assert await other.get_user_state(app_name="app", user_id="alice") == {"name": "Atri"}
    assert await other.get_session(app_name="app", user_id="bob", session_id="s") is None
    next_session = await other.create_session(app_name="app", user_id="alice")
    assert next_session.state["user:name"] == "Atri"
    await other.delete_session(app_name="app", user_id="alice", session_id="s")
    assert await other.get_session(app_name="app", user_id="alice", session_id="s") is None


async def test_stale_session_rejected(tmp_path):
    service = JsonSessionService(tmp_path / "sessions.json")
    first = await service.create_session(app_name="a", user_id="u", session_id="s")
    stale = await service.get_session(app_name="a", user_id="u", session_id="s")
    await service.append_event(first, Event(author="user"))
    with pytest.raises(ValueError, match="Stale"):
        await service.append_event(stale, Event(author="user"))
