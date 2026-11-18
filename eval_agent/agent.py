"""Separate ADK evaluation entry point with a fixed clock and isolated data."""

import os
from datetime import UTC, datetime
from pathlib import Path

from booking_agent.agent import build_agent
from booking_agent.config import Settings
from booking_agent.service import BookingService
from booking_agent.storage.json_store import JsonStore

settings = Settings(data_dir=Path(os.environ.get("BOOKING_EVAL_DIR", "artifacts/eval-runtime")))
service = BookingService(
    JsonStore(settings.data_dir / "bookings.json"),
    settings,
    clock=lambda: datetime(2030, 1, 7, tzinfo=UTC),
)
root_agent = build_agent(service, settings)
