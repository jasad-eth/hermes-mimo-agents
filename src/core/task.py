"""
Task — unit of work dispatched to agents.
"""

from __future__ import annotations

import uuid
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class TaskStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TaskResult:
    """Output produced by an agent after completing a task."""

    task_id: str
    agent_id: str
    output: str
    artifacts: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: Optional[str] = None
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "output": self.output,
            "artifacts": self.artifacts,
            "success": self.success,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "metadata": self.metadata,
        }


@dataclass
class Task:
    """A discrete unit of work to be executed by an agent."""

    description: str
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    assigned_to: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL
    dependencies: list[str] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    result: Optional[TaskResult] = None
    max_retries: int = 2
    retry_count: int = 0
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None

    def assign(self, agent_id: str) -> None:
        self.assigned_to = agent_id
        self.status = TaskStatus.ASSIGNED

    def start(self) -> None:
        self.status = TaskStatus.IN_PROGRESS
        self.started_at = time.time()

    def complete(self, result: TaskResult) -> None:
        self.result = result
        self.status = TaskStatus.COMPLETED
        self.completed_at = time.time()

    def fail(self, error: str) -> None:
        self.status = TaskStatus.FAILED
        self.completed_at = time.time()
        if self.result:
            self.result.success = False
            self.result.error = error

    def cancel(self) -> None:
        self.status = TaskStatus.CANCELLED
        self.completed_at = time.time()

    def can_retry(self) -> bool:
        return self.retry_count < self.max_retries

    def retry(self) -> None:
        self.retry_count += 1
        self.status = TaskStatus.PENDING
        self.started_at = None
        self.completed_at = None
        self.result = None

    @property
    def duration_ms(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at) * 1000
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "assigned_to": self.assigned_to,
            "status": self.status.value,
            "priority": self.priority.value,
            "dependencies": self.dependencies,
            "retry_count": self.retry_count,
            "duration_ms": self.duration_ms,
        }
