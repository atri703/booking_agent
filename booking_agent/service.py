"""Deterministic booking rules. LLM tools may propose; only clients may commit."""

from datetime import UTC, date, datetime, time, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

from booking_agent.config import Settings
from booking_agent.models import Booking, BookingInput, ProposalRequest
from booking_agent.storage.json_store import Store


class BookingError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


class BookingService:
    def __init__(self, store: Store, settings: Settings, clock=None):
        self.store = store
        self.settings = settings
        self.zone = ZoneInfo(settings.timezone)
        self.clock = clock or (lambda: datetime.now(UTC))

    def _validate_slot(self, booking: BookingInput):
        local = booking.start.astimezone(self.zone)
        # Reject impossible local times represented with an arbitrary offset by
        # interpreting the supplied instant in the configured business timezone.
        end = local + timedelta(minutes=booking.duration_minutes)
        if booking.resource != self.settings.resource:
            raise BookingError("invalid_resource", "Unknown booking resource")
        if local <= self.clock().astimezone(self.zone):
            raise BookingError("past_slot", "Appointment must be in the future")
        if local > self.clock().astimezone(self.zone) + timedelta(days=90):
            raise BookingError("outside_horizon", "Appointments can be booked up to 90 days ahead")
        if (
            local.weekday() >= 5
            or local.hour < 9
            or end.date() != local.date()
            or end.time() > time(17)
            or local.minute not in (0, 30)
            or local.second
            or local.microsecond
        ):
            raise BookingError("outside_hours", "Use weekdays 09:00–17:00 on a 30-minute grid")

    def _owned(self, state, booking_id, owner):
        item = state["bookings"].get(booking_id)
        if not item or item["owner"] != owner:
            raise BookingError("not_found", "Booking not found")
        return item

    def _free(self, state, booking, exclude=None):
        start = booking.start.astimezone(UTC)
        end = start + timedelta(minutes=booking.duration_minutes)
        for item in state["bookings"].values():
            if item["id"] == exclude or item["resource"] != booking.resource:
                continue
            other = datetime.fromisoformat(item["start"]).astimezone(UTC)
            if start < other + timedelta(minutes=item["duration_minutes"]) and other < end:
                raise BookingError("conflict", "That slot is no longer available")

    def list_bookings(self, owner):
        return sorted(
            [b for b in self.store.read()["bookings"].values() if b["owner"] == owner],
            key=lambda b: b["start"],
        )

    def get_booking(self, owner, booking_id):
        return self._owned(self.store.read(), booking_id, owner)

    def availability(self, day: str, duration_minutes: int = 30):
        if duration_minutes not in (30, 60):
            raise BookingError("invalid_duration", "Duration must be 30 or 60 minutes")
        target = date.fromisoformat(day)
        state = self.store.read()
        slots = []
        for minute in range(9 * 60, 17 * 60, 30):
            start = datetime.combine(target, time(minute // 60, minute % 60), self.zone)
            booking = BookingInput(
                customer_name="availability",
                start=start,
                duration_minutes=duration_minutes,
                resource=self.settings.resource,
            )
            try:
                self._validate_slot(booking)
                self._free(state, booking)
            except BookingError:
                continue
            slots.append(start.isoformat())
        return {"date": day, "timezone": self.settings.timezone, "slots": slots}

    def propose(self, owner: str, request: ProposalRequest):
        def operation(state):
            if request.action == "create":
                if request.booking is None or request.booking_id or request.expected_version:
                    raise BookingError("invalid_request", "Create requires only booking details")
            else:
                old = self._owned(state, request.booking_id, owner)
                if request.expected_version != old["version"]:
                    raise BookingError(
                        "stale_version", "Fetch the latest booking before changing it"
                    )
            if request.action in ("create", "update"):
                if request.booking is None:
                    raise BookingError("invalid_request", "Complete booking details are required")
                self._validate_slot(request.booking)
                self._free(state, request.booking, request.booking_id)
            elif request.booking is not None:
                raise BookingError("invalid_request", "Delete does not accept booking details")
            # The latest proposal replaces unconfirmed changes in this conversation.
            for proposal in state["proposals"].values():
                if (
                    proposal["owner"] == owner
                    and proposal["request"]["session_id"] == request.session_id
                    and proposal["status"] == "pending"
                ):
                    proposal["status"] = "superseded"
            proposal = {
                "id": str(uuid4()),
                "owner": owner,
                "status": "pending",
                "expires_at": (self.clock() + timedelta(minutes=10)).isoformat(),
                "request": request.model_dump(mode="json"),
            }
            state["proposals"][proposal["id"]] = proposal
            return proposal

        return self.store.transact(operation)

    def pending(self, owner, session_id):
        return [
            p
            for p in self.store.read()["proposals"].values()
            if p["owner"] == owner
            and p["request"]["session_id"] == session_id
            and p["status"] == "pending"
            and datetime.fromisoformat(p["expires_at"]) > self.clock()
        ]

    def confirm(self, owner: str, proposal_id: str):
        def operation(state):
            proposal = state["proposals"].get(proposal_id)
            if not proposal or proposal["owner"] != owner:
                raise BookingError("not_found", "Proposal not found")
            if proposal["status"] == "committed":
                return proposal["result"]  # Retry after a lost response is safe.
            if proposal["status"] != "pending":
                raise BookingError("superseded", "This proposal has been replaced")
            if datetime.fromisoformat(proposal["expires_at"]) <= self.clock():
                raise BookingError("expired", "Proposal expired; request a new one")
            request = ProposalRequest.model_validate(proposal["request"])
            if request.action != "create":
                old = self._owned(state, request.booking_id, owner)
                if old["version"] != request.expected_version:
                    raise BookingError("stale_version", "Booking changed since the proposal")
            if request.action == "delete":
                del state["bookings"][request.booking_id]
                result = {"action": "delete", "booking_id": request.booking_id, "deleted": True}
            else:
                self._validate_slot(request.booking)
                self._free(state, request.booking, request.booking_id)
                booking = Booking(
                    **request.booking.model_dump(),
                    owner=owner,
                    id=request.booking_id or str(uuid4()),
                    version=1 if request.action == "create" else old["version"] + 1,
                ).model_dump(mode="json")
                state["bookings"][booking["id"]] = booking
                result = {"action": request.action, "booking": booking}
            proposal.update(status="committed", result=result)
            state["audit"].append(
                {
                    "proposal_id": proposal_id,
                    "action": request.action,
                    "timestamp": self.clock().isoformat(),
                }
            )
            return result

        return self.store.transact(operation)
