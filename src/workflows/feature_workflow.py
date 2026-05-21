"""
Feature Development Workflow — Planner designs, Coder implements, Reviewer validates.
"""

from ..core.orchestrator import Orchestrator
from ..core.task import Task, TaskPriority


async def feature_development_workflow(
    orchestrator: Orchestrator,
    feature_request: str,
    tech_stack: str = "Python",
) -> dict:
    """
    Hierarchical workflow:
    1. Planner decomposes feature into tasks
    2. Coder implements each subtask
    3. Reviewer validates the complete implementation
    """
    # Phase 1: Planning
    plan_task = Task(
        description=(
            f"Create an implementation plan for this feature:\n\n"
            f"{feature_request}\n\n"
            f"Tech stack: {tech_stack}\n"
            "Break it into concrete, implementable steps."
        ),
        assigned_to="planner",
        priority=TaskPriority.HIGH,
        context={"tech_stack": tech_stack},
    )

    plan_result = await orchestrator.run_sequential([plan_task])

    if not plan_result.success:
        return {
            "success": False,
            "error": "Planning phase failed",
            "duration_ms": plan_result.total_duration_ms,
        }

    plan_output = plan_task.result.output if plan_task.result else ""

    # Phase 2: Implementation (parallel subtasks)
    implement_task = Task(
        description=(
            f"Implement the following plan:\n\n{plan_output}\n\n"
            f"Write complete, runnable {tech_stack} code."
        ),
        assigned_to="coder",
        priority=TaskPriority.HIGH,
        context={"plan": plan_output, "tech_stack": tech_stack},
    )

    impl_result = await orchestrator.run_sequential([implement_task])

    # Phase 3: Review
    code_output = implement_task.result.output if implement_task.result else ""

    review_task = Task(
        description=(
            f"Review the complete implementation:\n\n{code_output}\n\n"
            "Check against the original plan. Verify all requirements met."
        ),
        assigned_to="reviewer",
        priority=TaskPriority.NORMAL,
        context={"original_plan": plan_output, "feature_request": feature_request},
    )

    review_result = await orchestrator.run_sequential([review_task])

    return {
        "success": impl_result.success and review_result.success,
        "plan": plan_output,
        "implementation": code_output,
        "review": review_task.result.output if review_task.result else "",
        "total_duration_ms": (
            plan_result.total_duration_ms
            + impl_result.total_duration_ms
            + review_result.total_duration_ms
        ),
    }
