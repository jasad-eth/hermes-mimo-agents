"""
Message — atomic communication unit between agents.
"""

from __future__ import annotations

import uuid
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    AGENT = "agent"


@dataclass
class Message:
    """A single message in an agent conversation."""

    role: MessageRole
    content: str
    sender: str = "user"
    recipient: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role.value,
            "content": self.content,
            "sender": self.sender,
            "recipient": self.recipient,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }

    def to_llm_message(self) -> dict[str, str]:
        """Convert to OpenAI-compatible message format."""
        return {"role": self.role.value, "content": self.content}

    @classmethod
    def system(cls, content: str) -> Message:
        return cls(role=MessageRole.SYSTEM, content=content, sender="system")

    @classmethod
    def user(cls, content: str, sender: str = "user") -> Message:
        return cls(role=MessageRole.USER, content=content, sender=sender)

    @classmethod
    def assistant(cls, content: str, sender: str = "assistant") -> Message:
        return cls(role=MessageRole.ASSISTANT, content=content, sender=sender)

    @classmethod
    def agent(cls, content: str, sender: str, recipient: str = "") -> Message:
        return cls(
            role=MessageRole.AGENT,
            content=content,
            sender=sender,
            recipient=recipient,
        )
