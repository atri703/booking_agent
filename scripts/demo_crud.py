"""Offline full CRUD smoke test in a temporary JSON file; never touches runtime data."""

import tempfile
from datetime import UTC, datetime
from pathlib import Path

from booking_agent.config import Settings
from booking_agent.models import BookingInput, ProposalRequest
from booking_agent.service import BookingService
from booking_agent.storage.json_store import JsonStore


def main():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory)
        service = BookingService(
            JsonStore(path / "bookings.json"),
            Settings(data_dir=path),
            clock=lambda: datetime(2030, 1, 7, tzinfo=UTC),
        )
        details = BookingInput(customer_name="Demo", start="2030-01-08T10:00:00+05:30")
        p = service.propose("demo", ProposalRequest(action="create", booking=details))
        b = service.confirm("demo", p["id"])["booking"]
        assert service.get_booking("demo", b["id"]) == b
        changed = details.model_copy(update={"customer_name": "Updated Demo"})
        p = service.propose(
            "demo",
            ProposalRequest(
                action="update", booking_id=b["id"], expected_version=1, booking=changed
            ),
        )
        assert service.confirm("demo", p["id"])["booking"]["customer_name"] == "Updated Demo"
        p = service.propose(
            "demo", ProposalRequest(action="delete", booking_id=b["id"], expected_version=2)
        )
        service.confirm("demo", p["id"])
        assert service.list_bookings("demo") == []
        print("PASS: create, read, update and delete on a temporary JSON file; no API keys or DB.")


if __name__ == "__main__":
    main()
