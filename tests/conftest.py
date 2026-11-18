from datetime import UTC, datetime

import pytest

from booking_agent.config import Settings
from booking_agent.service import BookingService
from booking_agent.storage.json_store import JsonStore
from booking_agent.storage.sqlite_store import SQLiteStore

NOW = datetime(2030, 1, 7, 0, 0, tzinfo=UTC)  # Monday; fixture clock never ages.


@pytest.fixture(params=["json", "sqlite"])
def service(request, tmp_path):
    store = (
        JsonStore(tmp_path / "bookings.json")
        if request.param == "json"
        else SQLiteStore(tmp_path / "bookings.sqlite")
    )
    return BookingService(store, Settings(data_dir=tmp_path), clock=lambda: NOW)
