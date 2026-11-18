"""Optional coordinator delegates booking work over a real A2A transport."""

import httpx
from google.adk.agents import LlmAgent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.agent_tool import AgentTool

from booking_agent.config import Settings


def build_coordinator(settings=None, model=None, client=None):
    settings = settings or Settings.from_env()
    headers = {"Authorization": f"Bearer {settings.api_token}"} if settings.api_token else {}
    remote = RemoteA2aAgent(
        name="booking_specialist",
        agent_card=settings.a2a_url + "/.well-known/agent-card.json",
        description="Find appointments and propose booking changes for review.",
        httpx_client=client or httpx.AsyncClient(headers=headers, timeout=60),
        timeout=60,
    )
    return LlmAgent(
        name="coordinator",
        model=model or LiteLlm(model=settings.model),
        instruction="""Delegate appointment requests to booking_specialist. Preserve exact user
        requirements and return its proposal ID and confirmation instructions. You cannot confirm
        a proposal. Do not invent results or describe proposed changes as completed bookings.
        The remote service is a single-user demo. Keep follow-up context when delegating.""",
        tools=[AgentTool(agent=remote)],
    )


root_agent = build_coordinator()
