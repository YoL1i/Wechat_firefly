\"\"\"WChat Agent - Entry point.\"\"\"

from __future__ import annotations

import asyncio
import os
import signal
import sys
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger


class WChatAgent:
    \"\"\"Main agent that orchestrates all components.\"\"\"

    def __init__(self):
        self._initialized = False
        self.bridge = None
        self.brain = None
        self.character = None
        self.emotion = None
        self.scheduler = None
        self.memory = None
        self.tts = None
        self.reminders = None
        self.initiative = None
        self._target_user = None

    def initialize(self) -> bool:
        \"\"\"Initialize all components.\"\"\"
        if self._initialized:
            return True

        logger.info("Initializing WChat Agent...")

        # Load config
        from wchat.config.loader import config
        config.load()
        logger.info("Config loaded")

        # Load character card
        char_name = config.get("character", "default", default="liuying")
        card_data = config.load_character_card(char_name)
        if not card_data:
            logger.error("Failed to load character card: {}", char_name)
            return False

        from wchat.core.character import Character
        self.character = Character(card_data)
        logger.info("Character loaded: {}", self.character.name)

        # Initialize components
        from wchat.core.emotions import EmotionEngine
        self.emotion = EmotionEngine(self.character.emotion_rules)

        from wchat.core.memory import ConversationMemory
        self.memory = ConversationMemory()

        from wchat.core.brain import DialogueEngine
        self.brain = DialogueEngine(self.character)

        from wchat.services.tts import TTSEngine
        self.tts = TTSEngine(self.character.voice_config)

        from wchat.services.reminders import ReminderService
        from wchat.services.initiative import InitiativeService

        self.reminders = ReminderService(
            card_data, self._send_message,
        )
        self.initiative = InitiativeService(
            card_data, self._send_message, self._get_emotion,
        )

        from wchat.core.scheduler import TaskScheduler
        self.scheduler = TaskScheduler()

        self._initialized = True
        logger.info("All components initialized")
        return True

    def connect_wechat(self) -> bool:
        \"\"\"Connect to WeChatFerry.\"\"\"
        from wchat.bridge.wechat import WeChatBridge
        self.bridge = WeChatBridge()
        if not self.bridge.connect():
            logger.error("WeChat connection failed")
            return False

        self.bridge.on_message(self._handle_message)
        self._target_user = self.bridge.get_self_wxid()
        logger.info("WeChat bridge connected")
        return True

    def _handle_message(self, msg) -> None:
        \"\"\"Handle incoming WeChat messages.\"\"\"
        from wchat.bridge.message import MessageType

        # Skip own messages and non-text
        if msg.is_self or not msg.is_text:
            return

        logger.info("Received: {} <- {}", msg.content[:50], msg.display_sender)

        # Update emotion
        self.emotion.update_on_message(msg.content)
        emotion_state = self.emotion.get_state_value()

        # Get conversation context
        context = self.memory.get_context()

        # Get AI response
        reply = self.brain.chat(msg.content, context, emotion_state)
        if not reply:
            return

        # Store in memory
        self.memory.add_turn("user", msg.content)
        self.memory.add_turn("assistant", reply)

        # Send reply
        self.bridge.send_text(msg.sender, reply)
        logger.info("Replied: {}...", reply[:40])

    def _send_message(self, text: str) -> bool:
        \"\"\"Send message to the target user.\"\"\"
        if not self.bridge or not self._target_user:
            logger.warning("Cannot send: no bridge or target")
            return False
        return self.bridge.send_text(self._target_user, text)

    def _get_emotion(self) -> str:
        \"\"\"Get current emotion state.\"\"\"
        if self.emotion:
            return self.emotion.get_state_value()
        return "happy"

    def _register_reminders(self) -> None:
        \"\"\"Register all scheduled reminders.\"\"\"
        if not self.scheduler or not self.reminders:
            return

        # Drink water: every 2 hours
        interval = int(self.scheduler.config.get(
            "scheduler", "drink_water_interval_minutes", default=120
        ))
        self.scheduler.add_interval_task(
            "drink_water",
            self.reminders.remind_drink_water,
            minutes=interval,
        )

        # Study reminders at specific hours
        study_hours = self.scheduler.config.get(
            "scheduler", "study_reminder_hours", default=[9, 14, 19]
        )
        for hour in study_hours:
            self.scheduler.add_cron_task(
                f"study_{hour}",
                self.reminders.remind_study,
                hour=int(hour),
            )

        # Time-based messages
        time_slots = {
            "morning": 7, "work_start": 9, "lunch": 12,
            "afternoon": 15, "evening": 18, "review": 21, "goodnight": 23,
        }
        for slot, hour in time_slots.items():
            self.scheduler.add_cron_task(
                f"time_{slot}",
                lambda s=slot: self.reminders.send_time_based(s),
                hour=hour,
            )

        # Heartfelt messages: once daily in the evening
        self.scheduler.add_cron_task(
            "heartfelt_daily",
            self.reminders.send_heartfelt,
            hour=20,
        )

        # Proactive messages: random intervals
        self.scheduler.add_interval_task(
            "initiative_check",
            self.initiative.send_proactive,
            minutes=30,
        )

        logger.info("All reminders registered")

    def setup_scheduler(self) -> None:
        from wchat.config.loader import config as cfg
        self.scheduler.config = cfg
        self._register_reminders()

    async def run(self, server_mode: bool = False) -> None:
        \"\"\"Run the agent.\"\"\"
        if not self._initialized:
            if not self.initialize():
                return

        if not self.connect_wechat():
            return

        self.setup_scheduler()
        self.scheduler.start()
        self.bridge.start_listening()

        logger.info("\\n=== WChat Agent is running ===")
        logger.info("Character: {}", self.character.name)
        logger.info("Server mode: {}", server_mode)
        logger.info("Press Ctrl+C to stop\\n")

        if server_mode:
            await self._run_server()
        else:
            await self._run_forever()

    async def _run_forever(self) -> None:
        \"\"\"Run indefinitely.\"\"\"
        try:
            while True:
                await asyncio.sleep(60)
        except asyncio.CancelledError:
            pass

    async def _run_server(self) -> None:
        \"\"\"Run in server mode (for hybrid deployment).\"\"\"
        from wchat.config.loader import config as cfg
        host = cfg.get("server", "host", default="0.0.0.0")
        port = int(cfg.get("server", "port", default=8765))

        logger.info("Starting WebSocket server on {}:{}", host, port)
        # WebSocket server will be implemented in Phase 8
        await self._run_forever()

    def shutdown(self) -> None:
        \"\"\"Graceful shutdown.\"\"\"
        logger.info("Shutting down...")
        if self.scheduler:
            self.scheduler.stop()
        if self.bridge:
            self.bridge.disconnect()
        logger.info("Shutdown complete")


async def main():
    \"\"\"Entry point.\"\"\"
    # Load .env
    load_dotenv()

    # Configure logging
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_file = os.getenv("LOG_FILE", "data/logs/wchat.log")
    logger.remove()
    logger.add(sys.stderr, level=log_level)
    logger.add(log_file, level="DEBUG", rotation="10 MB")

    # Create and run agent
    agent = WChatAgent()
    server_mode = os.getenv("SERVER_MODE", "false").lower() == "true"

    def _shutdown():
        agent.shutdown()
        sys.exit(0)

    try:
        await agent.run(server_mode=server_mode)
    except KeyboardInterrupt:
        _shutdown()


if __name__ == "__main__":
    asyncio.run(main())
