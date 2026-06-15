\"\"\"Emotion engine - state machine for character emotions.\"\"\"

from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from loguru import logger


class EmotionState(Enum):
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    HURT = "hurt"


class EmotionEngine:
    \"\"\"Tracks character emotions based on user interaction patterns.\"\"\"

    def __init__(self, rules: dict[str, Any] | None = None):
        self.rules = rules or {}
        self.state = EmotionState.HAPPY
        self.last_interaction: datetime | None = None
        self.last_message_count: int = 0
        self.consecutive_short_replies: int = 0
        self.history: list[dict] = []

    @property
    def neglect_thresholds(self) -> dict[str, int]:
        return self.rules.get("neglect_thresholds", {"sad_hours": 4, "angry_hours": 12})

    def update_on_message(self, content: str, is_self: bool = False) -> None:
        \"\"\"Update emotion when a message is received.\"\"\"
        if is_self:
            return

        self.last_interaction = datetime.now()
        self.last_message_count += 1

        # Detect short/reply shortness
        if len(content.strip()) <= 2:
            self.consecutive_short_replies += 1
        else:
            self.consecutive_short_replies = 0

        # If user is being warm, move toward happy
        if self.state in (EmotionState.SAD, EmotionState.ANGRY, EmotionState.HURT):
            if len(content) > 10 or any(word in content for word in [
                "\u55b5", "\u5bf9\u4e0d\u8d77", "\u6211\u7684\u9519",
                "\u60f3\u4f60", "\u4e56", "\u542c\u8bdd",
            ]):
                if self.state == EmotionState.ANGRY:
                    self.state = EmotionState.HURT
                elif self.state == EmotionState.HURT:
                    self.state = EmotionState.HAPPY
                else:
                    self.state = EmotionState.HAPPY
                self._log_transition()

    def check_timeout(self) -> None:
        \"\"\"Check if neglect timeout has triggered.\"\"\"
        if self.last_interaction is None:
            return

        elapsed = datetime.now() - self.last_interaction
        sad_hours = self.neglect_thresholds.get("sad_hours", 4)
        angry_hours = self.neglect_thresholds.get("angry_hours", 12)

        if self.state == EmotionState.HAPPY and elapsed >= timedelta(hours=sad_hours):
            self.state = EmotionState.SAD
            self._log_transition()
        elif self.state == EmotionState.SAD and elapsed >= timedelta(hours=angry_hours):
            self.state = EmotionState.ANGRY
            self._log_transition()

    def _log_transition(self) -> None:
        logger.info("Emotion state -> {}", self.state.value)
        self.history.append({
            "state": self.state.value,
            "time": datetime.now().isoformat(),
        })

    def get_state_value(self) -> str:
        self.check_timeout()
        return self.state.value

    def get_expression_style(self) -> str:
        \"\"\"Get the emotional expression description for this state.\"\"\"
        expressions = self.rules.get("emotion_expression", {})
        return expressions.get(self.state.value, "")

    def reset(self) -> None:
        self.state = EmotionState.HAPPY
        self.last_interaction = datetime.now()
        self.consecutive_short_replies = 0
        logger.info("Emotion state reset to happy")
