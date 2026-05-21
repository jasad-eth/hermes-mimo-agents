"""
Orchestrator — the brain that coordinates agents, tasks, and workflows.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from .agent import Agent, AgentConfig
from .task import Task, TaskStatus, TaskPriority, TaskResult
from .message import Message

logger = logging.getLogger(__name__)


class WorkflowMode(str, Enum):
    SEQUENTIAL = "sequential"      # Tasks run one after another
    PARALLEL = "parallel"          # Independent tasks run concurrently
    PIPELINE = "pipeline"          # Output of one feeds into next
    DEBATE = "debate"              # Multiple agents discuss and converge
    HIERARCHICAL = "hierarchical"  # Lead agent delegates to specialists


@dataclass
class WorkflowResult:
    """Aggregated result of a workflow execution."""

    workflow_id: str
    mode: WorkflowMode
    task_results: list[TaskResult] = field(default_factory=list)
    summary: str = ""
    total_duration_ms: float = 0.0
    success: bool = True

    @property
    def total_tokens(self) -> int:
        return sum(
            r.metadata.get("tokens", 0) for r in self.task_results
        )


class Orchestrator:
    """
    Multi-agent orchestrator that:
    - Registers and manages agents
    - Decomposes complex goals into tasks
    - Routes tasks to appropriate agents
    - Manages dependencies and execution order
    - Aggregates results
    """

    def __init__(self, mimo_client: Any, config: Optional[dict[str, Any]] = None):
        self.mimo = mimo_client
        self.config = config or {}
        self.agents: dict[str, Agent] = {}
        self.task_queue: list[Task] = []
        self.completed_tasks: list[Task] = []
        self.workflow_counter = 0
        self._event_log: list[dict[str, Any]] = []

        logger.info("Orchestrator initialized")

    # ── Agent Management ──────────────────────────────────────────

    def register_agent(self, config: AgentConfig) -> Agent:
        """Create and register a new agent."""
        agent = Agent(config, self.mimo)
        self.agents[config.name] = agent
        self._log_event("agent_registered", {"agent": config.name, "role": config.role})
        return agent

    def get_agent(self, name: str) -> Agent:
        if name not in self.agents:
            raise KeyError(f"Agent '{name}' not found. Available: {list(self.agents.keys())}")
        return self.agents[name]

    def list_agents(self) -> list[dict[str, Any]]:
        return [a.get_stats() for a in self.agents.values()]

    # ── Task Management ───────────────────────────────────────────

    def create_task(
        self,
        description: str,
        assigned_to: Optional[str] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        dependencies: Optional[list[str]] = None,
        context: Optional[dict[str, Any]] = None,
    ) -> Task:
        """Create a new task."""
        task = Task(
            description=description,
            assigned_to=assigned_to,
            priority=priority,
            dependencies=dependencies or [],
            context=context or {},
        )
        self.task_queue.append(task)
        self._log_event("task_created", {"task_id": task.id, "description": description[:60]})
        return task

    def _find_agent_for_task(self, task: Task) -> Agent:
        """Auto-route task to best-fit agent based on role/skills."""
        if task.assigned_to:
            return self.get_agent(task.assigned_to)

        # Simple heuristic: match task keywords to agent roles
        task_lower = task.description.lower()
        best_agent = None
        best_score = 0

        for agent in self.agents.values():
            score = 0
            role_lower = agent.config.role.lower()
            tools = [t.lower() for t in agent.config.tools]

            # Role matching
            for word in role_lower.split():
                if word in task_lower:
                    score += 3

            # Tool matching
            for tool in tools:
                if tool in task_lower:
                    score += 2

            if score > best_score:
                best_score = score
                best_agent = agent

        # Fallback to first available agent
        if not best_agent:
            best_agent = list(self.agents.values())[0]

        task.assign(best_agent.id)
        return best_agent

    # ── Workflow Execution ─────────────────────────────────────────

    async def run_sequential(self, tasks: list[Task]) -> WorkflowResult:
        """Execute tasks sequentially, passing context forward."""
        self.workflow_counter += 1
        wf_id = f"wf-{self.workflow_counter}"
        result = WorkflowResult(workflow_id=wf_id, mode=WorkflowMode.SEQUENTIAL)
        start = time.time()

        context_chain: dict[str, Any] = {}

        for task in tasks:
            # Merge previous results into context
            if context_chain:
                task.context["previous_results"] = context_chain

            agent = self._find_agent_for_task(task)
            task_result = await agent.execute_task(task)
            result.task_results.append(task_result)

            if task_result.success:
                context_chain[task.id] = task_result.output
                self.completed_tasks.append(task)
            else:
                result.success = False
                if task.can_retry():
                    task.retry()
                    # Retry with same agent
                    task_result = await agent.execute_task(task)
                    if task_result.success:
                        context_chain[task.id] = task_result.output
                        result.success = True

        result.total_duration_ms = (time.time() - start) * 1000
        self._log_event("workflow_completed", {"id": wf_id, "mode": "sequential"})
        return result

    async def run_parallel(self, tasks: list[Task]) -> WorkflowResult:
        """Execute independent tasks concurrently."""
        self.workflow_counter += 1
        wf_id = f"wf-{self.workflow_counter}"
        result = WorkflowResult(workflow_id=wf_id, mode=WorkflowMode.PARALLEL)
        start = time.time()

        async def run_one(task: Task) -> TaskResult:
            agent = self._find_agent_for_task(task)
            return await agent.execute_task(task)

        task_results = await asyncio.gather(
            *[run_one(t) for t in tasks], return_exceptions=True
        )

        for task, tr in zip(tasks, task_results):
            if isinstance(tr, Exception):
                result.task_results.append(
                    TaskResult(
                        task_id=task.id,
                        agent_id="unknown",
                        output="",
                        success=False,
                        error=str(tr),
                    )
                )
                result.success = False
            else:
                result.task_results.append(tr)
                if tr.success:
                    self.completed_tasks.append(task)
                else:
                    result.success = False

        result.total_duration_ms = (time.time() - start) * 1000
        self._log_event("workflow_completed", {"id": wf_id, "mode": "parallel"})
        return result

    async def run_pipeline(self, stages: list[list[Task]]) -> WorkflowResult:
        """Execute pipeline: each stage's output feeds into the next stage."""
        self.workflow_counter += 1
        wf_id = f"wf-{self.workflow_counter}"
        result = WorkflowResult(workflow_id=wf_id, mode=WorkflowMode.PIPELINE)
        start = time.time()
        pipeline_context: dict[str, Any] = {}

        for stage_idx, stage_tasks in enumerate(stages):
            logger.info(f"Pipeline stage {stage_idx + 1}/{len(stages)}")

            # Inject pipeline context
            for task in stage_tasks:
                task.context["pipeline_context"] = pipeline_context

            if len(stage_tasks) == 1:
                agent = self._find_agent_for_task(stage_tasks[0])
                tr = await agent.execute_task(stage_tasks[0])
                result.task_results.append(tr)
                if tr.success:
                    pipeline_context[f"stage_{stage_idx}"] = tr.output
                else:
                    result.success = False
                    break
            else:
                # Parallel within stage
                stage_result = await self.run_parallel(stage_tasks)
                result.task_results.extend(stage_result.task_results)
                if stage_result.success:
                    outputs = [
                        tr.output for tr in stage_result.task_results if tr.success
                    ]
                    pipeline_context[f"stage_{stage_idx}"] = outputs
                else:
                    result.success = False
                    break

        result.total_duration_ms = (time.time() - start) * 1000
        self._log_event("workflow_completed", {"id": wf_id, "mode": "pipeline"})
        return result

    async def run_debate(
        self, topic: str, agents: list[str], rounds: int = 3
    ) -> WorkflowResult:
        """
        Debate mode: multiple agents discuss a topic and converge on a conclusion.
        Each agent sees previous arguments and refines their position.
        """
        self.workflow_counter += 1
        wf_id = f"wf-{self.workflow_counter}"
        result = WorkflowResult(workflow_id=wf_id, mode=WorkflowMode.DEBATE)
        start = time.time()

        debate_history: list[dict[str, str]] = []

        for round_num in range(rounds):
            logger.info(f"Debate round {round_num + 1}/{rounds}")

            for agent_name in agents:
                agent = self.get_agent(agent_name)

                # Build debate prompt
                prompt = f"## Debate Topic\n{topic}\n\n"
                if debate_history:
                    prompt += "## Previous Arguments\n"
                    for entry in debate_history:
                        prompt += f"**{entry['agent']}**: {entry['argument']}\n\n"
                    prompt += (
                        f"\n## Your Turn (Round {round_num + 1})\n"
                        "Respond to previous arguments. "
                        "Refine your position. Be concise and specific."
                    )
                else:
                    prompt += (
                        f"## Opening Statement (Round 1)\n"
                        "Present your initial analysis and position."
                    )

                task = Task(description=prompt, priority=TaskPriority.HIGH)
                tr = await agent.execute_task(task)
                result.task_results.append(tr)

                if tr.success:
                    debate_history.append({
                        "agent": agent_name,
                        "argument": tr.output,
                        "round": round_num + 1,
                    })

        # Final synthesis
        if self.agents:
            synthesizer = list(self.agents.values())[0]
            synthesis_prompt = (
                f"## Debate Synthesis\n\nTopic: {topic}\n\n"
                "## All Arguments\n"
            )
            for entry in debate_history:
                synthesis_prompt += f"**{entry['agent']}** (R{entry['round']}): {entry['argument'][:500]}\n\n"
            synthesis_prompt += (
                "\n## Task\n"
                "Synthesize all arguments into a final, balanced conclusion. "
                "Highlight key agreements and remaining disagreements."
            )

            synthesis_task = Task(description=synthesis_prompt, priority=TaskPriority.CRITICAL)
            synthesis_result = await synthesizer.execute_task(synthesis_task)
            result.task_results.append(synthesis_result)
            result.summary = synthesis_result.output if synthesis_result.success else ""

        result.total_duration_ms = (time.time() - start) * 1000
        result.success = all(tr.success for tr in result.task_results)
        self._log_event("workflow_completed", {"id": wf_id, "mode": "debate"})
        return result

    # ── Event Logging ─────────────────────────────────────────────

    def _log_event(self, event_type: str, data: dict[str, Any]) -> None:
        self._event_log.append({
            "type": event_type,
            "data": data,
            "timestamp": time.time(),
        })

    def get_event_log(self) -> list[dict[str, Any]]:
        return self._event_log

    def get_stats(self) -> dict[str, Any]:
        return {
            "agents": len(self.agents),
            "tasks_queued": len(self.task_queue),
            "tasks_completed": len(self.completed_tasks),
            "workflows_run": self.workflow_counter,
            "events_logged": len(self._event_log),
        }
