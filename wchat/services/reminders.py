\"\"\"Reminder service - drink water, study, and custom reminders.\"\"\"

from __future__ import annotations

import random
from typing import Any, Callable

from loguru import logger


class ReminderService:
    \"\"\"Sends periodic reminders through WeChat.\"\"\"

    def __init__(self, character_data: dict[str, Any],
                 send_func: Callable):
        self.character = character_data
        self.send = send_func
        self.interactions = character_data.get("interactions", {})
        self.reminder_config = self.interactions.get("reminders", {})

    def remind_drink_water(self) -> None:
        \"\"\"Send a drink water reminder.\"\"\"
        messages = self.reminder_config.get("drink_water", [])
        if messages:
            msg = random.choice(messages)
            self._send_reminder(msg)
            logger.info("Sent drink water reminder")

    def remind_study(self) -> None:
        \"\"\"Send a study reminder.\"\"\"
        messages = self.reminder_config.get("study", [])
        if messages:
            msg = random.choice(messages)
            self._send_reminder(msg)
            logger.info("Sent study reminder")

    def send_time_based(self, slot: str) -> None:
        \"\"\"Send a time-based greeting.\"\"\"
        time_based = self.interactions.get("time_based", {})
        slot_data = time_based.get(slot)
        if slot_data and slot_data.get("messages"):
            msg = random.choice(slot_data["messages"])
            self._send_reminder(msg)
            logger.info("Sent time-based message: {}", slot)

    def send_heartfelt(self) -> None:
        \"\"\"Send a random heartfelt message.\"\"\"
        heartfelt = self.interactions.get("heartfelt", [])
        if heartfelt:
            msg = random.choice(heartfelt)
            self._send_reminder(msg)
            logger.info("Sent heartfelt message")

    def _send_reminder(self, message: str) -> None:
        \"\"\"Send reminder via the WeChat bridge.\"\"\"
        try:
            self.send(message)
        except Exception as e:
            logger.error("Failed to send reminder: {}", e)
