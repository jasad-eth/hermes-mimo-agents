"""
Demo: Dry-run showcase (no API key needed)

Demonstrates the framework's architecture and message flow
without making actual API calls. Useful for reviewers.
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.message import Message
from src.core.task import Task, TaskPriority, TaskResult
from src.core.agent import AgentConfig


def print_header(text: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}")


def print_section(text: str) -> None:
    print(f"\n--- {text} ---")


async def main():
    print_header("🤖 Hermes-MiMo Multi-Agent Framework — Dry Run Demo")

    # ── 1. Show Agent Configs ────────────────────────────────
    print_section("1. Agent Definitions")

    from src.agents import CoderAgent, ReviewerAgent, ResearcherAgent, PlannerAgent

    agents = [CoderAgent(), ReviewerAgent(), ResearcherAgent(), PlannerAgent()]
    for cfg in agents:
        print(f"  🤖 {cfg.name:12s} | {cfg.role:35s} | temp={cfg.temperature}")

    # ── 2. Show Message Flow ─────────────────────────────────
    print_section("2. Inter-Agent Message Flow")

    messages = [
        Message.system("You are a senior coder."),
        Message.user("Write a rate limiter in Python"),
        Message.assistant("Here's a token bucket implementation...", sender="coder"),
        Message.agent("Review this code for edge cases", sender="coder", recipient="reviewer"),
        Message.agent("Found 2 issues: race condition, missing timeout", sender="reviewer", recipient="coder"),
    ]

    for msg in messages:
        icon = {"system": "⚙️", "user": "👤", "assistant": "🤖", "agent": "📨"}[msg.role.value]
        sender = msg.sender.ljust(12)
        content = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
        print(f"  {icon} [{sender}] → {content}")

    # ── 3. Show Task Lifecycle ───────────────────────────────
    print_section("3. Task Lifecycle")

    task = Task(
        description="Implement rate limiter middleware",
        priority=TaskPriority.HIGH,
    )
    print(f"  📋 Created:    {task.id} | status={task.status.value}")

    task.assign("coder-agent")
    print(f"  🎯 Assigned:   status={task.status.value} → {task.assigned_to}")

    task.start()
    print(f"  🔄 In Progress: status={task.status.value}")

    result = TaskResult(
        task_id=task.id,
        agent_id="coder-agent",
        output="```python\nclass TokenBucket:\n    def __init__(self, rate, capacity):\n        ...\n```",
        duration_ms=1234.5,
        success=True,
    )
    task.complete(result)
    print(f"  ✅ Completed:  status={task.status.value} | {result.duration_ms:.0f}ms")

    # ── 4. Show Workflow Modes ───────────────────────────────
    print_section("4. Available Workflow Modes")

    from src.core.orchestrator import WorkflowMode
    descriptions = {
        WorkflowMode.SEQUENTIAL: "Tasks run one by one, context passes forward",
        WorkflowMode.PARALLEL: "Independent tasks run concurrently",
        WorkflowMode.PIPELINE: "Stage output feeds into next stage",
        WorkflowMode.DEBATE: "Multiple agents argue, then synthesize",
        WorkflowMode.HIERARCHICAL: "Lead agent delegates to specialists",
    }
    for mode in WorkflowMode:
        print(f"  🔄 {mode.value:15s} | {descriptions[mode]}")

    # ── 5. Show Architecture ─────────────────────────────────
    print_section("5. Architecture")

    print("""
    ┌─────────────────────────────────────────────┐
    │              Orchestrator                    │
    │  ┌────────┐  ┌────────┐  ┌────────┐        │
    │  │Planner │  │ Coder  │  │Reviewer│  ...    │
    │  └───┬────┘  └───┬────┘  └───┬────┘        │
    │      └───────────┼───────────┘              │
    │                  │                           │
    │          ┌───────▼───────┐                  │
    │          │  MiMo v2.5    │                  │
    │          │  API Backend  │                  │
    │          └───────────────┘                  │
    └─────────────────────────────────────────────┘
    """)

    print_header("✅ Demo complete — all components working!")


if __name__ == "__main__":
    asyncio.run(main())
