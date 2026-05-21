"""
Example: Multi-Agent Debate

Demonstrates the debate workflow where multiple agents
discuss a technical topic and converge on a conclusion.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.utils.mimo_client import MiMoClient
from src.core.orchestrator import Orchestrator
from src.agents import CoderAgent, ReviewerAgent, ResearcherAgent


async def main():
    api_key = os.getenv("MIMO_API_KEY", "your-api-key-here")
    base_url = os.getenv("MIMO_BASE_URL", "https://token-plan-sgp.xiaomimimo.com/v1")

    async with MiMoClient(api_key=api_key, base_url=base_url) as mimo:
        orch = Orchestrator(mimo_client=mimo)

        # Register agents with different perspectives
        orch.register_agent(CoderAgent())
        orch.register_agent(ReviewerAgent())
        orch.register_agent(ResearcherAgent())

        topic = (
            "Should we use GraphQL or REST for a high-traffic "
            "microservices architecture? Consider performance, "
            "developer experience, and operational complexity."
        )

        print("🗣️ Multi-Agent Debate")
        print("=" * 60)
        print(f"Topic: {topic}")
        print(f"Participants: {list(orch.agents.keys())}")
        print(f"Rounds: 3")
        print("=" * 60)

        result = await orch.run_debate(
            topic=topic,
            agents=["coder", "reviewer", "researcher"],
            rounds=3,
        )

        print(f"\n{'=' * 60}")
        print(f"📊 Debate Result")
        print(f"   Success: {result.success}")
        print(f"   Duration: {result.total_duration_ms:.0f}ms")
        print(f"   Arguments: {len(result.task_results)}")
        print(f"\n🎯 Final Synthesis:\n")
        print(result.summary[:1000] if result.summary else "No synthesis available")


if __name__ == "__main__":
    asyncio.run(main())
