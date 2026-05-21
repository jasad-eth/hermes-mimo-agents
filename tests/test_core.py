"""
Tests for core components.
"""

import pytest
from src.core.message import Message, MessageRole
from src.core.task import Task, TaskStatus, TaskPriority, TaskResult


class TestMessage:
    def test_create_system_message(self):
        msg = Message.system("You are a helpful assistant")
        assert msg.role == MessageRole.SYSTEM
        assert msg.content == "You are a helpful assistant"
        assert msg.sender == "system"

    def test_create_user_message(self):
        msg = Message.user("Hello", sender="alice")
        assert msg.role == MessageRole.USER
        assert msg.sender == "alice"

    def test_to_llm_message(self):
        msg = Message.user("test")
        llm_msg = msg.to_llm_message()
        assert llm_msg == {"role": "user", "content": "test"}

    def test_to_dict(self):
        msg = Message.assistant("response")
        d = msg.to_dict()
        assert "id" in d
        assert "timestamp" in d
        assert d["role"] == "assistant"


class TestTask:
    def test_create_task(self):
        task = Task(description="Write a function")
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.NORMAL

    def test_task_lifecycle(self):
        task = Task(description="Test task")
        assert task.status == TaskStatus.PENDING

        task.assign("agent-1")
        assert task.status == TaskStatus.ASSIGNED

        task.start()
        assert task.status == TaskStatus.IN_PROGRESS

        result = TaskResult(
            task_id=task.id,
            agent_id="agent-1",
            output="Done!",
            success=True,
        )
        task.complete(result)
        assert task.status == TaskStatus.COMPLETED
        assert task.result.success is True

    def test_task_failure_and_retry(self):
        task = Task(description="Failing task", max_retries=2)
        task.start()
        task.fail("Error occurred")
        assert task.status == TaskStatus.FAILED
        assert task.can_retry()

        task.retry()
        assert task.status == TaskStatus.PENDING
        assert task.retry_count == 1

    def test_task_priority(self):
        task = Task(description="Urgent", priority=TaskPriority.CRITICAL)
        assert task.priority == TaskPriority.CRITICAL

    def test_task_dependencies(self):
        task = Task(description="Depends on others", dependencies=["task-1", "task-2"])
        assert len(task.dependencies) == 2


class TestTaskResult:
    def test_result_to_dict(self):
        result = TaskResult(
            task_id="t1",
            agent_id="a1",
            output="result text",
            artifacts=["file.py"],
            duration_ms=150.5,
        )
        d = result.to_dict()
        assert d["task_id"] == "t1"
        assert d["success"] is True
        assert d["duration_ms"] == 150.5
