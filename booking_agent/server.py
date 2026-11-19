"""Local-first REST, chat and A2A server. No model credentials needed for CRUD."""

import asyncio
import logging
import os
import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents.run_config import RunConfig
from google.adk.runners import Runner
from google.genai import types
from pydantic import Field

from booking_agent.agent import build_agent
from booking_agent.config import Settings, model_api_key_name
from booking_agent.models import Confirmation, ProposalRequest, StrictModel
from booking_agent.service import BookingError, BookingService
from booking_agent.sessions import JsonSessionService
from booking_agent.storage.json_store import JsonStore
from booking_agent.tools import DEMO_OWNER

logger = logging.getLogger(__name__)


class ChatRequest(StrictModel):
    message: str = Field(min_length=1, max_length=8000)
    session_id: str | None = Field(default=None, min_length=1, max_length=100)


def create_app(settings=None, model=None, clock=None):
    settings = settings or Settings.from_env()
    store = JsonStore(settings.data_dir / "bookings.json")
    service = BookingService(store, settings, clock=clock)
    sessions = JsonSessionService(settings.data_dir / "sessions.json")
    agent = build_agent(service, settings, model=model)
    runner = Runner(agent=agent, app_name="booking_agent", session_service=sessions)
    parsed = urlparse(settings.a2a_url)
    a2a = to_a2a(
        agent,
        runner=runner,
        host=parsed.hostname or "127.0.0.1",
        port=parsed.port or 8001,
        protocol=parsed.scheme or "http",
    )
    locks = {}

    @asynccontextmanager
    async def lifespan(app):
        async with a2a.router.lifespan_context(a2a):
            yield
        await runner.close()

    app = FastAPI(title="Booking Agent", version="0.1.0", lifespan=lifespan)
    app.state.service = service
    app.state.sessions = sessions
    app.state.runner = runner

    @app.middleware("http")
    async def local_auth(request: Request, call_next):
        public_request = request.url.path == "/health" or (
            request.method == "GET" and request.url.path == "/"
        )
        if settings.api_token and not public_request:
            token = request.headers.get("authorization", "")
            if not secrets.compare_digest(token, "Bearer " + settings.api_token):
                return JSONResponse({"detail": "Unauthorized"}, status_code=401)
        return await call_next(request)

    @app.exception_handler(BookingError)
    async def booking_error(request, exc):
        status = 404 if exc.code == "not_found" else 409
        return JSONResponse({"error": exc.code, "message": str(exc)}, status_code=status)

    @app.get("/health")
    def health():
        return {"status": "ok", "storage": "json", "mode": "single-user-local-demo"}

    @app.get("/", response_class=HTMLResponse)
    def index():
        return Path(__file__).with_name("index.html").read_text(encoding="utf-8")

    @app.get("/api/policy")
    def policy():
        return {
            "timezone": settings.timezone,
            "resource": settings.resource,
            "now": service.clock().astimezone(service.zone).isoformat(),
        }

    @app.get("/api/availability")
    def availability(day: str, duration_minutes: int = 30):
        try:
            return service.availability(day, duration_minutes)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc

    @app.get("/api/bookings")
    def bookings():
        return service.list_bookings(DEMO_OWNER)

    @app.get("/api/bookings/{booking_id}")
    def booking(booking_id: str):
        return service.get_booking(DEMO_OWNER, booking_id)

    @app.post("/api/proposals", status_code=201)
    def propose(body: ProposalRequest):
        return service.propose(DEMO_OWNER, body)

    @app.get("/api/proposals")
    def proposals(session_id: str):
        return service.pending(DEMO_OWNER, session_id)

    @app.post("/api/proposals/{proposal_id}/confirm")
    def confirm(proposal_id: str, body: Confirmation):
        return service.confirm(DEMO_OWNER, proposal_id)

    @app.get("/api/sessions/{session_id}")
    async def history(session_id: str):
        session = await sessions.get_session(
            app_name="booking_agent", user_id=DEMO_OWNER, session_id=session_id
        )
        if not session:
            raise HTTPException(404, "Session not found")
        return session.model_dump(mode="json")

    @app.post("/api/chat")
    async def chat(body: ChatRequest):
        api_key_name = model_api_key_name(settings.model)
        if model is None and not os.getenv(api_key_name):
            raise HTTPException(503, f"Set {api_key_name} to use chat. JSON CRUD works without it.")
        session_id = body.session_id or str(uuid4())
        lock = locks.setdefault(session_id, asyncio.Lock())
        async with lock:
            if not await sessions.get_session(
                app_name="booking_agent", user_id=DEMO_OWNER, session_id=session_id
            ):
                await sessions.create_session(
                    app_name="booking_agent", user_id=DEMO_OWNER, session_id=session_id
                )
            try:
                final = []
                async with asyncio.timeout(120):
                    async for event in runner.run_async(
                        user_id=DEMO_OWNER,
                        session_id=session_id,
                        new_message=types.Content(
                            role="user", parts=[types.Part(text=body.message)]
                        ),
                        run_config=RunConfig(max_llm_calls=12),
                    ):
                        if event.is_final_response() and event.content:
                            final.extend(p.text for p in event.content.parts or [] if p.text)
                return {
                    "session_id": session_id,
                    "message": "\n".join(final),
                    "proposals": service.pending(DEMO_OWNER, session_id),
                }
            except TimeoutError as exc:
                raise HTTPException(504, "Agent timed out; no confirmation was performed") from exc
            except Exception as exc:
                logger.error("Agent request failed: %s", type(exc).__name__)
                raise HTTPException(
                    502, "Agent request failed; check server configuration"
                ) from exc

    app.mount("/", a2a)
    return app


app = create_app()
