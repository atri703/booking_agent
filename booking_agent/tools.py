"""Only read and proposal tools are exposed to the language model."""

from google.adk.tools import ToolContext
from pydantic import ValidationError

from booking_agent.models import BookingInput, ProposalRequest
from booking_agent.service import BookingError, BookingService

DEMO_OWNER = "demo-user"


def build_tools(service: BookingService):
    def safe(operation):
        try:
            return operation()
        except (BookingError, ValidationError, ValueError) as exc:
            return {"error": getattr(exc, "code", "invalid_input"), "message": str(exc)}

    def booking_policy() -> dict:
        """Get current date/time, business timezone, hours, services and confirmation rules."""
        return {
            "now": service.clock().astimezone(service.zone).isoformat(),
            "timezone": service.settings.timezone,
            "resource": service.settings.resource,
            "hours": "Monday–Friday 09:00–17:00",
            "duration_minutes": [30, 60],
            "services": ["consultation", "follow_up"],
            "horizon_days": 90,
            "confirmation": "Confirm the returned proposal through the client UI or REST.",
        }

    def find_available_slots(day: str, duration_minutes: int = 30) -> dict:
        """Find slots for an ISO date (YYYY-MM-DD) in the business timezone."""
        return safe(lambda: service.availability(day, duration_minutes))

    def list_my_bookings() -> dict:
        """Read the local demo user's bookings, including their IDs and versions."""
        return {"bookings": service.list_bookings(DEMO_OWNER)}

    def propose_booking(
        customer_name: str,
        start: str,
        duration_minutes: int,
        service_name: str,
        tool_context: ToolContext,
    ) -> dict:
        """Prepare a new appointment for human confirmation. start must include a UTC offset."""
        return safe(
            lambda: service.propose(
                DEMO_OWNER,
                ProposalRequest(
                    action="create",
                    session_id=tool_context.session.id,
                    booking=BookingInput(
                        customer_name=customer_name,
                        start=start,
                        duration_minutes=duration_minutes,
                        service=service_name,
                        resource=service.settings.resource,
                    ),
                ),
            )
        )

    def propose_reschedule(
        booking_id: str,
        expected_version: int,
        customer_name: str,
        start: str,
        duration_minutes: int,
        service_name: str,
        tool_context: ToolContext,
    ) -> dict:
        """Prepare an update using the latest booking version, for human confirmation."""
        return safe(
            lambda: service.propose(
                DEMO_OWNER,
                ProposalRequest(
                    action="update",
                    session_id=tool_context.session.id,
                    booking_id=booking_id,
                    expected_version=expected_version,
                    booking=BookingInput(
                        customer_name=customer_name,
                        start=start,
                        duration_minutes=duration_minutes,
                        service=service_name,
                        resource=service.settings.resource,
                    ),
                ),
            )
        )

    def propose_cancellation(
        booking_id: str, expected_version: int, tool_context: ToolContext
    ) -> dict:
        """Prepare deletion of a booking for human confirmation."""
        return safe(
            lambda: service.propose(
                DEMO_OWNER,
                ProposalRequest(
                    action="delete",
                    session_id=tool_context.session.id,
                    booking_id=booking_id,
                    expected_version=expected_version,
                ),
            )
        )

    return [
        booking_policy,
        find_available_slots,
        list_my_bookings,
        propose_booking,
        propose_reschedule,
        propose_cancellation,
    ]
