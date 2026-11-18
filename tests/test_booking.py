import json
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from pydantic import ValidationError

from booking_agent.models import BookingInput, ProposalRequest
from booking_agent.service import BookingError
from booking_agent.storage.json_store import JsonStore


def details(start="2030-01-08T10:00:00+05:30", **changes):
    return BookingInput(**({"customer_name": "Atri", "start": start} | changes))


def propose(service, owner="alice", session="one", **kwargs):
    return service.propose(
        owner, ProposalRequest(action="create", session_id=session, booking=details(**kwargs))
    )


def create(service, **kwargs):
    p = propose(service, **kwargs)
    return service.confirm(kwargs.get("owner", "alice"), p["id"])["booking"]


def test_full_crud(service):
    p = propose(service)
    assert service.list_bookings("alice") == []
    b = service.confirm("alice", p["id"])["booking"]
    assert service.get_booking("alice", b["id"]) == b
    update = service.propose(
        "alice",
        ProposalRequest(
            action="update",
            booking_id=b["id"],
            expected_version=1,
            booking=details("2030-01-08T11:00:00+05:30"),
        ),
    )
    changed = service.confirm("alice", update["id"])["booking"]
    assert changed["version"] == 2
    assert changed["start"].startswith("2030-01-08T11:00")
    delete = service.propose(
        "alice", ProposalRequest(action="delete", booking_id=b["id"], expected_version=2)
    )
    assert service.confirm("alice", delete["id"])["deleted"]
    assert service.list_bookings("alice") == []
    assert len(service.store.read()["audit"]) == 3


@pytest.mark.parametrize(
    "start,code",
    [
        ("2030-01-06T10:00:00+05:30", "past_slot"),
        ("2030-06-08T10:00:00+05:30", "outside_horizon"),
        ("2030-01-12T10:00:00+05:30", "outside_hours"),
        ("2030-01-08T08:30:00+05:30", "outside_hours"),
        ("2030-01-08T17:00:00+05:30", "outside_hours"),
        ("2030-01-08T10:15:00+05:30", "outside_hours"),
        ("2030-01-08T10:00:01+05:30", "outside_hours"),
    ],
)
def test_invalid_slots(service, start, code):
    with pytest.raises(BookingError) as exc:
        propose(service, start=start)
    assert exc.value.code == code


@pytest.mark.parametrize(
    "change",
    [
        {"start": "2030-01-08T10:00:00"},
        {"customer_name": " "},
        {"duration_minutes": 45},
        {"service": "unknown"},
    ],
)
def test_schema_validation(change):
    with pytest.raises(ValidationError):
        details(**change)


def test_unknown_resource(service):
    with pytest.raises(BookingError, match="Unknown"):
        propose(service, resource="other")


def test_overlapping_slot_and_adjacent_slot(service):
    create(service, duration_minutes=60)
    with pytest.raises(BookingError, match="available"):
        propose(service, start="2030-01-08T10:30:00+05:30")
    create(service, start="2030-01-08T11:00:00+05:30")
    assert len(service.list_bookings("alice")) == 2


def test_timezone_equivalent_conflicts(service):
    create(service)
    with pytest.raises(BookingError, match="available"):
        propose(service, start="2030-01-08T04:30:00+00:00")


def test_last_slot_end_boundary(service):
    create(service, start="2030-01-08T16:30:00+05:30")
    with pytest.raises(BookingError, match="weekdays"):
        propose(service, start="2030-01-09T16:30:00+05:30", duration_minutes=60)


def test_no_foreign_reads_or_mutations(service):
    b = create(service)
    assert service.list_bookings("bob") == []
    with pytest.raises(BookingError, match="not found"):
        service.get_booking("bob", b["id"])
    with pytest.raises(BookingError, match="not found"):
        service.propose(
            "bob", ProposalRequest(action="delete", booking_id=b["id"], expected_version=1)
        )


def test_foreign_confirmation(service):
    p = propose(service)
    with pytest.raises(BookingError, match="not found"):
        service.confirm("bob", p["id"])


def test_repeat_confirmation_is_idempotent(service):
    p = propose(service)
    first = service.confirm("alice", p["id"])
    assert service.confirm("alice", p["id"]) == first
    assert len(service.list_bookings("alice")) == 1
    assert len(service.store.read()["audit"]) == 1


def test_new_proposal_invalidates_old_confirmation(service):
    p = propose(service)
    propose(service, start="2030-01-08T11:00:00+05:30")
    with pytest.raises(BookingError, match="replaced"):
        service.confirm("alice", p["id"])


def test_proposal_expiration(service):
    p = propose(service)
    now = service.clock()
    service.clock = lambda: now + timedelta(minutes=10)
    assert not service.pending("alice", "one")
    with pytest.raises(BookingError, match="expired"):
        service.confirm("alice", p["id"])


def test_concurrent_slot_race(service):
    proposals = [propose(service, owner=f"owner{i}") for i in range(8)]

    def commit(pair):
        i, p = pair
        try:
            service.confirm(f"owner{i}", p["id"])
            return "ok"
        except BookingError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(commit, enumerate(proposals)))
    assert results.count("ok") == 1
    assert results.count("conflict") == 7
    assert len(service.store.read()["bookings"]) == 1


def test_stale_update_does_not_overwrite(service):
    b = create(service)
    proposals = [
        service.propose(
            "alice",
            ProposalRequest(
                action="update",
                session_id=str(i),
                booking_id=b["id"],
                expected_version=1,
                booking=details(f"2030-01-08T{11 + i}:00:00+05:30"),
            ),
        )
        for i in range(2)
    ]
    service.confirm("alice", proposals[0]["id"])
    with pytest.raises(BookingError, match="changed"):
        service.confirm("alice", proposals[1]["id"])
    assert service.get_booking("alice", b["id"])["version"] == 2


def test_failed_reschedule_keeps_original(service):
    b = create(service)
    p = service.propose(
        "alice",
        ProposalRequest(
            action="update",
            booking_id=b["id"],
            expected_version=1,
            booking=details("2030-01-08T11:00:00+05:30"),
        ),
    )
    create(service, owner="bob", start="2030-01-08T11:00:00+05:30")
    with pytest.raises(BookingError, match="available"):
        service.confirm("alice", p["id"])
    assert service.get_booking("alice", b["id"]) == b


def test_availability(service):
    assert len(service.availability("2030-01-08")["slots"]) == 16
    create(service, duration_minutes=60)
    assert len(service.availability("2030-01-08")["slots"]) == 14
    assert service.availability("2030-01-12")["slots"] == []
    assert service.availability("2029-01-01")["slots"] == []


def test_transaction_rollback(service):
    before = service.store.read()

    def fail(state):
        state["bookings"]["bad"] = {}
        raise RuntimeError("fail")

    with pytest.raises(RuntimeError):
        service.store.transact(fail)
    assert service.store.read() == before


def test_corrupt_json_never_reset(tmp_path):
    path = tmp_path / "bookings.json"
    path.write_text("{broken")
    with pytest.raises(json.JSONDecodeError):
        JsonStore(path).transact(lambda d: None)
    assert path.read_text() == "{broken"


def test_persistence_across_instances(tmp_path):
    path = tmp_path / "bookings.json"
    JsonStore(path).transact(lambda state: state["bookings"].update({"a": {"name": "persist"}}))
    assert JsonStore(path).read()["bookings"]["a"]["name"] == "persist"
