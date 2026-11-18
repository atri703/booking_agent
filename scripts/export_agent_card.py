"""Export exactly the card served by this pinned ADK/A2A combination."""

import asyncio
import json
from pathlib import Path

from google.adk.a2a.utils.agent_card_builder import AgentCardBuilder
from google.protobuf.json_format import MessageToDict

from booking_agent.agent import root_agent
from booking_agent.config import Settings


async def main():
    card = await AgentCardBuilder(
        agent=root_agent, rpc_url=Settings.from_env().a2a_url + "/"
    ).build()
    Path("agent-card.json").write_text(json.dumps(MessageToDict(card), indent=2) + "\n")


if __name__ == "__main__":
    asyncio.run(main())
