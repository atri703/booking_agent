"""Persistent ADK sessions in JSON; no database connection is created."""

import json
import time
from uuid import uuid4

from google.adk.sessions import BaseSessionService, Session
from google.adk.sessions.base_session_service import ListSessionsResponse

from booking_agent.storage.json_store import JsonStore


class JsonSessionService(BaseSessionService):
    def __init__(self, path):
        self.store = JsonStore(
            path, lambda: {"schema_version": 1, "sessions": {}, "app_state": {}, "user_state": {}}
        )

    @staticmethod
    def _key(app_name, user_id, session_id):
        return json.dumps([app_name, user_id, session_id])

    def _merged(self, state, session):
        result = session.model_copy(deep=True)
        result.state.update(
            {"app:" + k: v for k, v in state["app_state"].get(session.app_name, {}).items()}
        )
        key = self._key(session.app_name, session.user_id, "")
        result.state.update({"user:" + k: v for k, v in state["user_state"].get(key, {}).items()})
        return result

    def _save(self, state, session):
        raw = session.model_dump(mode="json")
        app = state["app_state"].setdefault(session.app_name, {})
        user = state["user_state"].setdefault(self._key(session.app_name, session.user_id, ""), {})
        for key, value in session.state.items():
            if key.startswith("app:"):
                app[key[4:]] = value
            elif key.startswith("user:"):
                user[key[5:]] = value
        raw["state"] = {
            k: v for k, v in raw["state"].items() if not k.startswith(("temp:", "app:", "user:"))
        }
        state["sessions"][self._key(session.app_name, session.user_id, session.id)] = raw

    async def create_session(self, *, app_name, user_id, state=None, session_id=None):
        session = Session(
            id=session_id or str(uuid4()),
            app_name=app_name,
            user_id=user_id,
            state=state or {},
            last_update_time=time.time(),
        )

        def operation(document):
            key = self._key(app_name, user_id, session.id)
            if key in document["sessions"]:
                raise ValueError("Session already exists")
            self._save(document, session)
            return self._merged(document, session)

        return self.store.transact(operation)

    async def get_session(self, *, app_name, user_id, session_id, config=None):
        state = self.store.read()
        raw = state["sessions"].get(self._key(app_name, user_id, session_id))
        if not raw:
            return None
        session = self._merged(state, Session.model_validate(raw))
        if config:
            if config.after_timestamp is not None:
                session.events = [e for e in session.events if e.timestamp > config.after_timestamp]
            if config.num_recent_events is not None:
                count = config.num_recent_events
                session.events = session.events[-count:] if count > 0 else []
        return session

    async def list_sessions(self, *, app_name, user_id=None):
        sessions = []
        document = self.store.read()
        for raw in document["sessions"].values():
            if raw["app_name"] == app_name and (user_id is None or raw["user_id"] == user_id):
                session = self._merged(document, Session.model_validate(raw))
                session.events = []
                sessions.append(session)
        return ListSessionsResponse(sessions=sorted(sessions, key=lambda s: s.last_update_time))

    async def delete_session(self, *, app_name, user_id, session_id):
        self.store.transact(
            lambda doc: doc["sessions"].pop(self._key(app_name, user_id, session_id), None)
        )

    async def get_user_state(self, *, app_name, user_id):
        return self.store.read()["user_state"].get(self._key(app_name, user_id, ""), {})

    async def append_event(self, session, event):
        if event.partial:
            return event

        def operation(document):
            key = self._key(session.app_name, session.user_id, session.id)
            raw = document["sessions"].get(key)
            if raw is None:
                raise ValueError("Session no longer exists")
            if raw["last_update_time"] != session.last_update_time:
                raise ValueError("Stale session; reload before continuing")
            # Apply only this event to the full stored history, even if the caller
            # originally requested a filtered window of events.
            current = self._merged(document, Session.model_validate(raw))
            self._apply_temp_state(session, event)
            self._trim_temp_delta_state(event)
            self._commit_event_to_session(current, event)
            current.last_update_time = max(time.time(), current.last_update_time + 0.000001)
            self._save(document, current)
            return current

        saved = self.store.transact(operation)
        session.events = saved.events
        temp = {k: v for k, v in session.state.items() if k.startswith("temp:")}
        session.state = saved.state | temp
        session.last_update_time = saved.last_update_time
        return event
