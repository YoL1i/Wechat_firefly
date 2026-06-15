\"\"\"AI dialogue engine - interfaces with LLM APIs.\"\"\"

from __future__ import annotations

from typing import Any

from loguru import logger

from wchat.config.loader import config
from wchat.core.character import Character


class DialogueEngine:
    \"\"\"Manages LLM conversations with character context.\"\"\"

    def __init__(self, character: Character | None = None):
        self.character = character
        self._client = None

    def _get_client(self):
        \"\"\"Lazy-init the LLM client.\"\"\"
        if self._client is not None:
            return self._client

        provider = config.get("llm", "default", default="deepseek")
        api_key = config.get("llm", f"{provider}_api_key")

        if not api_key:
            logger.warning("No API key configured for {}", provider)
            return None

        base_urls = {
            "deepseek": "https://api.deepseek.com",
            "openai": "https://api.openai.com/v1",
        }

        try:
            from openai import OpenAI
            self._client = OpenAI(
                api_key=api_key,
                base_url=base_urls.get(provider, base_urls["deepseek"]),
            )
            logger.info("LLM client initialized: {}", provider)
        except Exception as e:
            logger.error("Failed to init LLM client: {}", e)
            return None
        return self._client

    def set_character(self, character: Character) -> None:
        self.character = character

    def chat(self, user_message: str, context: list[dict] | None = None,
             emotion_state: str | None = None) -> str:
        \"\"\"Send a message and get character's response.\"\"\"
        client = self._get_client()
        if not client:
            return self._fallback_reply(emotion_state)

        messages = self._build_messages(user_message, context, emotion_state)

        try:
            response = client.chat.completions.create(
                model=config.get("llm", "model", default="deepseek-chat"),
                messages=messages,
                temperature=0.8,
                max_tokens=500,
            )
            reply = response.choices[0].message.content or ""
            logger.debug("LLM reply: {}...", reply[:50])
            return reply
        except Exception as e:
            logger.error("LLM API error: {}", e)
            return self._fallback_reply(emotion_state)

    def _build_messages(self, user_msg: str, context: list[dict] | None,
                        emotion: str | None) -> list[dict]:
        messages = []

        # System prompt
        if self.character:
            system_prompt = self.character.build_system_prompt(emotion)
            messages.append({"role": "system", "content": system_prompt})

        # Recent conversation context
        if context:
            messages.extend(context)

        # Current message
        address = self.character.get_address(familiar=True) if self.character else ""
        if address:
            user_msg = f"({address} \u8bf4): {user_msg}"
        messages.append({"role": "user", "content": user_msg})
        return messages

    def _fallback_reply(self, emotion: str | None = None) -> str:
        \"\"\"Fallback reply when LLM is unavailable.\"\"\"
        if self.character:
            import random
            phrases = self.character.catchphrases
            if phrases:
                return random.choice(phrases)
        return "\u2026"
