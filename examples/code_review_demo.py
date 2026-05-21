"""
Example: Multi-Agent Code Review Pipeline

Demonstrates:
1. Setting up a MiMo client
2. Registering specialized agents
3. Running a code review pipeline workflow
4. Collecting and displaying results
"""

import asyncio
import os
import sys

# Add parent to path for local imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.utils.mimo_client import MiMoClient
from src.core.orchestrator import Orchestrator
from src.agents import CoderAgent, ReviewerAgent, PlannerAgent
from src.workflows import code_review_workflow


async def main():
    # ── Setup MiMo Client ─────────────────────────────────────
    api_key = os.getenv("MIMO_API_KEY", "your-api-key-here")
    base_url = os.getenv("MIMO_BASE_URL", "https://token-plan-sgp.xiaomimimo.com/v1")

    async with MiMoClient(api_key=api_key, base_url=base_url) as mimo:
        # ── Create Orchestrator ──────────────────────────────────
        orch = Orchestrator(mimo_client=mimo)

        # ── Register Agents ──────────────────────────────────────
        orch.register_agent(CoderAgent())
        orch.register_agent(ReviewerAgent())
        orch.register_agent(PlannerAgent())

        print("=" * 60)
        print("🤖 Hermes-MiMo Multi-Agent System")
        print("=" * 60)
        print(f"\nRegistered agents: {len(orch.agents)}")
        for stats in orch.list_agents():
            print(f"  • {stats['name']} ({stats['role']})")
        print()

        # ── Run Code Review Workflow ─────────────────────────────
        print("🔄 Running Code Review Pipeline...")
        print("-" * 40)

        result = await code_review_workflow(
            orchestrator=orch,
            feature_description=(
                "A rate limiter middleware for FastAPI that supports "
                "token bucket algorithm with Redis-backed distributed state"
            ),
            language="python",
        )

        # ── Display Results ──────────────────────────────────────
        print(f"\n✅ Workflow {result['workflow_id']} completed")
        print(f"   Success: {result['success']}")
        print(f"   Duration: {result['duration_ms']:.0f}ms")

        print("\n📝 Initial Code:")
        print(result["code"][:500] + "..." if len(result["code"]) > 500 else result["code"])

        print("\n🔍 Review:")
        print(result["review"][:500] + "..." if len(result["review"]) > 500 else result["review"])

        print("\n✅ Final Code:")
        print(result["final_code"][:500] + "..." if len(result["final_code"]) > 500 else result["final_code"])

        # ── Stats ────────────────────────────────────────────────
        print("\n📊 Session Stats:")
        print(f"   MiMo API: {mimo.get_stats()}")
        print(f"   Orchestrator: {orch.get_stats()}")


if __name__ == "__main__":
    asyncio.run(main())
