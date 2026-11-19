"""Expose the existing booking agent without duplicating application behavior."""

from booking_agent.agent import root_agent

__all__ = ["root_agent"]
