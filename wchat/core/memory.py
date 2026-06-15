\"\"\"Memory system - short-term conversation context and long-term storage.\"\"\"

from __future__ import annotations

from datetime import datetime
from typing import Any

from loguru import logger


class ConversationMemory:
    \"\"\"In-memory conversation context (short-term).\"\"\"

    def __init__(self, max_turns: int = 20):
        self.max_turns = max_turns
        self.turns: list[dict[str, Any]] = []
        self.notes: dict[str, str] = {}

    def add_turn(self, role: str, content: str) -> None:
        self.turns.append({
            "role": role,
            "content": content,
            "time": datetime.now().isoformat(),
        })
        if len(self.turns) > self.max_turns:
            self.turns.pop(0)

    def get_context(self, max_recent: int = 10) -> list[dict[str, str]]:
        \"\"\"Get recent conversation turns for LLM context.\"\"\"
        recent = self.turns[-max_recent:]
        return [{"role": t["role"], "content": t["content"]} for t in recent]

    def add_note(self, key: str, value: str) -> None:
        self.notes[key] = value
        logger.info("Memory note: {} = {}", key, value)

    def get_note(self, key: str, default: str | None = None) -> str | None:
        return self.notes.get(key, default)

    def clear(self) -> None:
        self.turns.clear()
        self.notes.clear()


class LongTermMemory:
    \"\"\"Persistent memory using SQLite (future).\"\"\"

    def __init__(self, db_path: str = "data/memory.db"):
        self.db_path = db_path
        self._ready = False

    async def init(self) -> None:
        \"\"\"Initialize database (placeholder).\"\"\"
        logger.info("Long-term memory not yet implemented, using in-memory only")
        self._ready = True
