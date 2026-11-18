import json

from fastapi.testclient import TestClient

from booking_agent.config import Settings
from booking_agent.server import create_app
from tests.conftest import NOW
from tests.fake_model import ScriptedModel


def test_offline_rest_crud(tmp_path):
    with TestClient(create_app(Settings(data_dir=tmp_path), clock=lambda: NOW)) as client:
        assert client.get("/health").json()["storage"] == "json"
        assert client.get("/").status_code == 200
        body = {
            "action": "create",
            "booking": {"customer_name": "Atri", "start": "2030-01-08T10:00:00+05:30"},
        }
        p = client.post("/api/proposals", json=body).json()
        assert client.get("/api/bookings").json() == []
        assert (
            client.post(f"/api/proposals/{p['id']}/confirm", json={"accepted": False}).status_code
            == 422
        )
        r = client.post(f"/api/proposals/{p['id']}/confirm", json={"accepted": True})
        b = r.json()["booking"]
        assert client.get("/api/bookings/" + b["id"]).json()["customer_name"] == "Atri"
        p = client.post(
            "/api/proposals",
            json={"action": "delete", "booking_id": b["id"], "expected_version": 1},
        ).json()
        assert (
            client.post(f"/api/proposals/{p['id']}/confirm", json={"accepted": True}).status_code
            == 200
        )
        assert client.get("/api/bookings").json() == []
        assert not list(tmp_path.glob("*.sqlite"))


def test_chat_executes_real_adk_tools_and_survives_restart(tmp_path):
    settings = Settings(data_dir=tmp_path)
    with TestClient(create_app(settings, model=ScriptedModel(), clock=lambda: NOW)) as client:
        r = client.post("/api/chat", json={"message": "prepare a booking", "session_id": "restore"})
        assert r.status_code == 200, r.text
        assert len(r.json()["proposals"]) == 1
        assert client.get("/api/bookings").json() == []
        assert "confirm" in r.json()["message"]
    with TestClient(create_app(settings, model=ScriptedModel(), clock=lambda: NOW)) as client:
        history = client.get("/api/sessions/restore").json()
        assert any(e["author"] == "user" for e in history["events"])
        p = client.get("/api/proposals?session_id=restore").json()[0]
        assert (
            client.post(f"/api/proposals/{p['id']}/confirm", json={"accepted": True}).status_code
            == 200
        )


def test_token_protects_crud_and_a2a(tmp_path):
    with TestClient(create_app(Settings(data_dir=tmp_path, api_token="secret"))) as client:
        for path in ["/api/bookings", "/.well-known/agent-card.json", "/api/sessions/x"]:
            assert client.get(path).status_code == 401
        assert client.post("/", json={}).status_code == 401
        assert client.get("/").status_code == 200
        assert (
            client.get("/api/bookings", headers={"Authorization": "Bearer secret"}).status_code
            == 200
        )


def test_missing_key_only_blocks_chat(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with TestClient(create_app(Settings(data_dir=tmp_path))) as client:
        assert client.post("/api/chat", json={"message": "hello"}).status_code == 503
        assert client.get("/api/bookings").status_code == 200


def test_agent_card_and_real_a2a_request(tmp_path):
    with TestClient(
        create_app(Settings(data_dir=tmp_path), model=ScriptedModel(), clock=lambda: NOW)
    ) as client:
        card = client.get("/.well-known/agent-card.json").json()
        assert card["supportedInterfaces"][0]["protocolVersion"] == "1.0"
        assert any("propose_booking" in s["id"] for s in card["skills"])
        assert not any("confirm" in s["id"] for s in card["skills"])
        r = client.post(
            "/",
            headers={"A2A-Version": "1.0"},
            json={
                "jsonrpc": "2.0",
                "id": "test",
                "method": "SendMessage",
                "params": {
                    "message": {
                        "messageId": "m1",
                        "role": "ROLE_USER",
                        "parts": [{"text": "prepare a booking"}],
                    }
                },
            },
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert "error" not in data, data
        assert "confirm" in json.dumps(data)
        assert client.get("/api/bookings").json() == []


async def test_coordinator_delegates_via_remote_a2a_agent(tmp_path):
    import httpx
    from google.adk.models.base_llm import BaseLlm
    from google.adk.models.llm_response import LlmResponse
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types

    from coordinator.agent import build_coordinator

    class DelegateModel(BaseLlm):
        model: str = "offline-coordinator"

        async def generate_content_async(self, llm_request, stream=False):
            last = llm_request.contents[-1]
            if any(p.function_response for p in last.parts):
                assert "confirm" in str(last), str(last)
                part = types.Part(text="Review the specialist proposal in the client.")
            else:
                part = types.Part(
                    function_call=types.FunctionCall(
                        name="booking_specialist", args={"request": "prepare a booking"}
                    )
                )
            yield LlmResponse(content=types.Content(role="model", parts=[part]))

    settings = Settings(data_dir=tmp_path, a2a_url="http://127.0.0.1:8001")
    app = create_app(settings, model=ScriptedModel(), clock=lambda: NOW)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url=settings.a2a_url
        ) as client:
            coordinator = build_coordinator(settings, DelegateModel(), client)
            sessions = InMemorySessionService()
            session = await sessions.create_session(app_name="coordinator", user_id="demo-user")
            runner = Runner(agent=coordinator, app_name="coordinator", session_service=sessions)
            events = [
                event
                async for event in runner.run_async(
                    user_id="demo-user",
                    session_id=session.id,
                    new_message=types.Content(
                        role="user", parts=[types.Part(text="prepare a booking")]
                    ),
                )
            ]
            assert any(e.is_final_response() for e in events)
            assert len(app.state.service.store.read()["proposals"]) == 1
            assert not app.state.service.list_bookings("demo-user")
            await runner.close()
