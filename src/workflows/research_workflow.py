"""
Research & Build Workflow — Researcher investigates, Planner structures, Coder builds.
"""

from ..core.orchestrator import Orchestrator
from ..core.task import Task, TaskPriority


async def research_and_build_workflow(
    orchestrator: Orchestrator,
    goal: str,
    constraints: str = "",
) -> dict:
    """
    Pipeline: Research → Plan → Build
    Best for: exploring new tech, building POCs, solving unfamiliar problems.
    """
    # Stage 1: Research
    research_task = Task(
        description=(
            f"Research the best approach for: {goal}\n"
            f"Constraints: {constraints or 'None'}\n\n"
            "Provide: technology recommendations, trade-offs, and a clear recommendation."
        ),
        assigned_to="researcher",
        priority=TaskPriority.HIGH,
        context={"goal": goal, "stage": "research"},
    )

    # Stage 2: Plan based on research
    plan_task = Task(
        description=(
            f"Based on the research findings, create a detailed implementation plan "
            f"for: {goal}"
        ),
        assigned_to="planner",
        priority=TaskPriority.HIGH,
        dependencies=[research_task.id],
        context={"stage": "planning"},
    )

    # Stage 3: Build
    build_task = Task(
        description=(
            f"Implement the plan. Write complete, production-ready code for: {goal}"
        ),
        assigned_to="coder",
        priority=TaskPriority.HIGH,
        dependencies=[plan_task.id],
        context={"stage": "building"},
    )

    # Run as pipeline
    result = await orchestrator.run_pipeline([
        [research_task],
        [plan_task],
        [build_task],
    ])

    return {
        "success": result.success,
        "research": research_task.result.output if research_task.result else "",
        "plan": plan_task.result.output if plan_task.result else "",
        "implementation": build_task.result.output if build_task.result else "",
        "duration_ms": result.total_duration_ms,
    }
