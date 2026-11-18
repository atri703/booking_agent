"""Strict domain schemas shared by tools, REST and storage."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BookingInput(StrictModel):
    customer_name: str = Field(min_length=1, max_length=100)
    start: datetime
    duration_minutes: Literal[30, 60] = 30
    service: Literal["consultation", "follow_up"] = "consultation"
    resource: str = Field(default="advisor", min_length=1, max_length=80)

    @field_validator("customer_name")
    @classmethod
    def name_not_blank(cls, value):
        if not value.strip():
            raise ValueError("customer_name cannot be blank")
        return value.strip()

    @field_validator("start")
    @classmethod
    def timezone_required(cls, value):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("start must include a UTC offset")
        return value


class Booking(BookingInput):
    id: str
    owner: str
    version: int = 1


class ProposalRequest(StrictModel):
    action: Literal["create", "update", "delete"]
    session_id: str = Field(default="demo", min_length=1, max_length=100)
    booking: BookingInput | None = None
    booking_id: str | None = None
    expected_version: int | None = Field(default=None, ge=1)


class Confirmation(StrictModel):
    accepted: Literal[True]
