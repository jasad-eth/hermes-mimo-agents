"""
Hermes-MiMo Multi-Agent Workflow Engine
========================================
A lightweight multi-agent orchestration framework powered by Xiaomi MiMo LLM.

Agents collaborate through structured message passing, task decomposition,
and intelligent routing — all running on MiMo's high-performance inference API.

Author: Warmad (Mad)
License: MIT
"""

__version__ = "0.1.0"
__author__ = "Warmad"

from .core.orchestrator import Orchestrator
from .core.agent import Agent
from .core.task import Task, TaskResult
from .core.message import Message

__all__ = ["Orchestrator", "Agent", "Task", "TaskResult", "Message"]
