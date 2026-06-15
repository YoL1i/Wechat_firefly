\"\"\"Proactive messaging service - randomly reaches out to the user.\"\"\"

from __future__ import annotations

import random
from typing import Any, Callable

from loguru import logger


class InitiativeService:
    \"\"\"Sends proactive messages based on character personality and emotion.\"\"\"

    def __init__(self, character_data: dict[str, Any],
                 send_func: Callable,
                 get_emotion_func: Callable):
        self.character = character_data
        self.send = send_func
        self.get_emotion = get_emotion_func
        self.init_cfg = character_data.get("initiative", {})
        self.interactions = character_data.get("interactions", {})
        self._daily_count = 0
        self._last_date = None

    def _check_new_day(self) -> None:
        from datetime import date
        today = date.today()
        if self._last_date != today:
            self._daily_count = 0
            self._last_date = today

    def get_random_message(self, emotion_state: str | None = None) -> str | None:
        \"\"\"Get a random proactive message.\"\"\"
        scenarios = self.init_cfg.get("scenarios", [])
        if not scenarios:
            return None

        msg = random.choice(scenarios)

        # Inject emotional flavor
        if emotion_state == "sad":
            msg += "\n\u2026\u2026\u4f60\u4f1a\u538c\u70e6\u5417\uff1f"
        elif emotion_state == "angry":
            msg += "\n\u7b97\u4e86\u3002\u4f60\u5fd9\u5427\u3002"

        return msg

    def should_send(self) -> bool:
        \"\"\"Check if we should send a proactive message now.\"\"\"
        self._check_new_day()

        daily_min = self.init_cfg.get("daily_min", 1)
        daily_max = self.init_cfg.get("daily_max", 3)

        if self._daily_count >= daily_max:
            return False

        # Frequency increases in sad/angry states
        emotion = self.get_emotion()
        if emotion in ("sad", "angry"):
            probability = 0.4
        else:
            probability = 0.2

        return random.random() < probability

    def send_proactive(self) -> bool:
        \"\"\"Try to send a proactive message. Returns True if sent.\"\"\"
        if not self.should_send():
            return False

        msg = self.get_random_message(self.get_emotion())
        if not msg:
            return False

        try:
            self.send(msg)
            self._daily_count += 1
            logger.info("Sent proactive message ({}/{}): {}...",
                        self._daily_count,
                        self.init_cfg.get("daily_max", 3),
                        msg[:30])
            return True
        except Exception as e:
            logger.error("Failed to send proactive message: {}", e)
            return False
