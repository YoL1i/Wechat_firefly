\"\"\"Message models for WeChat messages.\"\"\"

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class MessageType(Enum):
    TEXT = 1
    IMAGE = 3
    VOICE = 34
    FRIEND_REQUEST = 37
    SYSTEM = 10000
    UNKNOWN = 0


class MessageDirection(Enum):
    INCOMING = "in"
    OUTGOING = "out"


@dataclass
class WeChatMessage:
    \"\"\"Normalized WeChat message model.\"\"\"

    msg_id: int = 0
    msg_type: MessageType = MessageType.UNKNOWN
    direction: MessageDirection = MessageDirection.INCOMING
    sender: str = ""
    sender_name: str = ""
    room_id: str | None = None
    content: str = ""
    raw: Any = None
    timestamp: datetime = field(default_factory=datetime.now)
    is_self: bool = False
    is_group: bool = False

    @property
    def is_text(self) -> bool:
        return self.msg_type == MessageType.TEXT

    @property
    def display_sender(self) -> str:
        return self.sender_name or self.sender

    def reply(self, text: str) -> dict:
        \"\"\"Create a reply payload.\"\"\"
        return {
            "to": self.sender if not self.is_group else self.room_id,
            "content": text,
            "is_group": self.is_group,
        }


@dataclass
class OutgoingMessage:
    \"\"\"Message to be sent.\"\"\"
    target: str
    content: str
    msg_type: MessageType = MessageType.TEXT
    is_group: bool = False
    voice_path: str | None = None

    def to_wcf_payload(self) -> tuple:
        if self.msg_type == MessageType.VOICE and self.voice_path:
            return ("send_voice", {
                "receiver": self.target,
                "file_path": self.voice_path,
            })
        return ("send_text", {
            "receiver": self.target,
            "msg": self.content,
        })
