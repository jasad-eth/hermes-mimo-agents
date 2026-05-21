"""
Code Review Workflow — Coder writes, Reviewer reviews, Coder fixes.
"""

from ..core.orchestrator import Orchestrator
from ..core.task import Task, TaskPriority


async def code_review_workflow(
    orchestrator: Orchestrator,
    feature_description: str,
    language: str = "python",
) -> dict:
    """
    Pipeline: Coder writes code → Reviewer reviews → Coder fixes issues.

    Returns dict with code, review, and final_code.
    """
    # Stage 1: Write code
    write_task = Task(
        description=(
            f"Write {language} code for: {feature_description}\n"
            "Include error handling, type hints, and docstrings."
        ),
        assigned_to="coder",
        priority=TaskPriority.HIGH,
        context={"language": language, "stage": "implementation"},
    )

    # Stage 2: Review
    review_task = Task(
        description=(
            f"Review the following {language} code for bugs, security issues, "
            f"and improvements:\n\nFeature: {feature_description}"
        ),
        assigned_to="reviewer",
        priority=TaskPriority.HIGH,
        dependencies=[write_task.id],
        context={"stage": "review"},
    )

    # Stage 3: Fix based on review
    fix_task = Task(
        description=(
            "Fix all CRITICAL and WARNING issues from the review. "
            "Apply suggested improvements. Output the complete fixed code."
        ),
        assigned_to="coder",
        priority=TaskPriority.HIGH,
        dependencies=[review_task.id],
        context={"stage": "fix"},
    )

    # Run as pipeline
    result = await orchestrator.run_pipeline([
        [write_task],      # Stage 1
        [review_task],     # Stage 2
        [fix_task],        # Stage 3
    ])

    return {
        "workflow_id": result.workflow_id,
        "success": result.success,
        "code": write_task.result.output if write_task.result else "",
        "review": review_task.result.output if review_task.result else "",
        "final_code": fix_task.result.output if fix_task.result else "",
        "duration_ms": result.total_duration_ms,
    }
