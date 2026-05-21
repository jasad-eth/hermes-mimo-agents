"""
Agent — autonomous unit with a role, tools, and LLM backbone.
"""

from __future__ import annotations

import uuid
import time
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from .message import Message, MessageRole
from .task import Task, TaskResult

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Configuration for an agent."""

    name: str
    role: str
    system_prompt: str
    model: str = "MiMo-v2.5-pro"
    temperature: float = 0.7
    max_tokens: int = 2048
    max_history: int = 20
    tools: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class Agent:
    """
    An autonomous agent that:
    - Maintains conversation history
    - Executes tasks using LLM inference
    - Can delegate subtasks to other agents
    - Produces structured TaskResults
    """

    def __init__(self, config: AgentConfig, llm_client: Any):
        self.id = uuid.uuid4().hex[:8]
        self.config = config
        self.llm = llm_client
        self.history: list[Message] = []
        self.task_count = 0
        self.total_tokens_used = 0
        self._tool_registry: dict[str, Callable] = {}

        # Inject system prompt
        self.history.append(Message.system(config.system_prompt))

        logger.info(f"Agent [{self.config.name}] initialized (id={self.id})")

    def register_tool(self, name: str, func: Callable) -> None:
        """Register a callable tool for this agent."""
        self._tool_registry[name] = func
        logger.debug(f"Agent [{self.config.name}] registered tool: {name}")

    def _build_messages(self, user_input: str) -> list[dict[str, str]]:
        """Build message list for LLM API call."""
        messages = [m.to_llm_message() for m in self.history[-self.config.max_history:]]
        messages.append({"role": "user", "content": user_input})
        return messages

    async def think(self, prompt: str) -> str:
        """Send prompt to LLM and get response. Updates history."""
        messages = self._build_messages(prompt)

        try:
            response = await self.llm.chat(
                model=self.config.model,
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )

            content = response.content
            tokens = getattr(response, "usage", None)

            # Update history
            self.history.append(Message.user(prompt))
            self.history.append(Message.assistant(content, sender=self.config.name))

            if tokens:
                self.total_tokens_used += getattr(tokens, "total_tokens", 0)

            return content

        except Exception as e:
            logger.error(f"Agent [{self.config.name}] LLM error: {e}")
            raise

    async def execute_task(self, task: Task) -> TaskResult:
        """Execute a task and return structured result."""
        start = time.time()
        task.start()
        self.task_count += 1

        logger.info(
            f"Agent [{self.config.name}] executing task {task.id}: "
            f"{task.description[:60]}..."
        )

        try:
            # Build task prompt with context
            prompt = self._build_task_prompt(task)
            output = await self.think(prompt)

            duration = (time.time() - start) * 1000
            result = TaskResult(
                task_id=task.id,
                agent_id=self.id,
                output=output,
                duration_ms=duration,
                success=True,
            )
            task.complete(result)
            logger.info(
                f"Agent [{self.config.name}] completed task {task.id} "
                f"in {duration:.0f}ms"
            )
            return result

        except Exception as e:
            duration = (time.time() - start) * 1000
            error_msg = str(e)
            result = TaskResult(
                task_id=task.id,
                agent_id=self.id,
                output="",
                duration_ms=duration,
                success=False,
                error=error_msg,
            )
            task.fail(error_msg)
            logger.error(f"Agent [{self.config.name}] failed task {task.id}: {e}")
            return result

    def _build_task_prompt(self, task: Task) -> str:
        """Build a prompt for task execution."""
        parts = [f"## Task\n{task.description}"]

        if task.context:
            parts.append(f"\n## Context\n{self._format_context(task.context)}")

        if task.dependencies:
            parts.append(
                f"\n## Dependencies\nPrevious task IDs: {', '.join(task.dependencies)}"
            )

        parts.append(
            "\n## Instructions\n"
            "Provide a clear, actionable response. "
            "If producing code, ensure it's complete and runnable."
        )

        return "\n".join(parts)

    @staticmethod
    def _format_context(ctx: dict[str, Any]) -> str:
        lines = []
        for k, v in ctx.items():
            lines.append(f"- **{k}**: {v}")
        return "\n".join(lines)

    def receive_message(self, message: Message) -> None:
        """Receive a message from another agent."""
        self.history.append(message)

    def send_message(self, content: str, recipient: str) -> Message:
        """Create a message to send to another agent."""
        msg = Message.agent(content, sender=self.config.name, recipient=recipient)
        self.history.append(msg)
        return msg

    def get_stats(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.config.name,
            "role": self.config.role,
            "model": self.config.model,
            "tasks_completed": self.task_count,
            "total_tokens_used": self.total_tokens_used,
            "history_length": len(self.history),
            "tools_registered": list(self._tool_registry.keys()),
        }
