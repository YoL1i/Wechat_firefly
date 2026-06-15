\"\"\"Character card system - manages character personality and behavior.\"\"\"

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from loguru import logger


class Character:
    \"\"\"Represents a game character loaded from a character card.\"\"\"

    def __init__(self, card_data: dict[str, Any], card_path: Path | None = None):
        self.data = card_data
        self.card_path = card_path
        self._validate()

    def _validate(self) -> None:
        required = ["name", "personality"]
        for key in required:
            if key not in self.data:
                logger.warning("Character card missing required field: {}", key)

    @property
    def name(self) -> str:
        return self.data.get("name", "Unknown")

    @property
    def alias(self) -> str:
        return self.data.get("alias", "")

    @property
    def traits(self) -> list[str]:
        return self.data.get("personality", {}).get("traits", [])

    @property
    def speaking_style(self) -> str:
        return self.data.get("personality", {}).get("speaking_style", "")

    @property
    def catchphrases(self) -> list[str]:
        return self.data.get("personality", {}).get("catchphrases", [])

    @property
    def background(self) -> str:
        return self.data.get("background", "")

    @property
    def voice_config(self) -> dict[str, Any]:
        return self.data.get("voice", {})

    @property
    def emotion_rules(self) -> dict[str, Any]:
        return self.data.get("emotion_rules", {})

    @property
    def initiative_config(self) -> dict[str, Any]:
        return self.data.get("initiative", {})

    @property
    def sam_mode(self) -> dict[str, Any]:
        return self.data.get("sam_mode", {"enabled": False})

    @property
    def interactions(self) -> dict[str, Any]:
        return self.data.get("interactions", {})

    def get_relationship(self) -> dict[str, Any]:
        return self.data.get("relationship", {})

    def get_address(self, familiar: bool = False) -> str:
        rel = self.get_relationship()
        if familiar:
            return rel.get("address_familiar", "\u4f60")
        return rel.get("address_formal", "\u4f60")

    def build_system_prompt(self, emotion_state: str | None = None) -> str:
        \"\"\"Build the full system prompt for LLM with character context.\"\"\"
        prompt = f"You are {self.name}"
        if self.alias:
            prompt += f" ({self.alias})"
        prompt += f" from {self.data.get('from', '')}.\\n\\n"
        prompt += f"Background: {self.background}\\n\\n"
        prompt += f"Personality: {', '.join(self.traits)}\\n"
        prompt += f"Speaking style: {self.speaking_style}\\n\\n"

        if emotion_state:
            prompt += f"Current emotional state: {emotion_state}\\n"

        prompt += "\\nImportant rules:\\n"
        prompt += "- Stay in character at all times\\n"
        prompt += "- Use short, natural sentences\\n"
        prompt += "- Never break character or mention you are an AI\\n"
        return prompt

    def to_dict(self) -> dict[str, Any]:
        return self.data

    @classmethod
    def from_file(cls, path: str | Path) -> Character:
        path = Path(path)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        logger.info("Loaded character: {} from {}", data.get("name"), path)
        return cls(data, path)
