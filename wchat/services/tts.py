\"\"\"Text-to-speech service using Edge-TTS.\"\"\"

from __future__ import annotations

import asyncio
import os
import tempfile
from typing import Any

from loguru import logger


class TTSEngine:
    \"\"\"Voice message generation using Edge-TTS.\"\"\"

    def __init__(self, voice_config: dict[str, Any] | None = None):
        self.voice_config = voice_config or {}
        self._voice_name = "zh-CN-XiaoxiaoNeural"
        self._pitch = self.voice_config.get("pitch", "0Hz")
        self._rate = self.voice_config.get("rate", "+0%")
        self._ready = False

    def configure(self, voice_config: dict[str, Any]) -> None:
        self.voice_config = voice_config
        style = voice_config.get("style", "")
        if "\u6e29\u67d4" in style:
            self._pitch = "0Hz"
            self._rate = "-5%"
        elif "\u575a\u5b9a" in style:
            self._pitch = "-20Hz"
            self._rate = "+0%"
        else:
            self._pitch = voice_config.get("pitch", "0Hz")
            self._rate = voice_config.get("rate", "+0%")

    async def speak(self, text: str, output_path: str | None = None) -> str | None:
        \"\"\"Convert text to speech and return the audio file path.\"\"\"
        if not text.strip():
            return None

        if output_path is None:
            fd, output_path = tempfile.mkstemp(suffix=".wav")
            os.close(fd)

        try:
            import edge_tts
            communicate = edge_tts.Communicate(
                text,
                voice=self._voice_name,
                pitch=self._pitch,
                rate=self._rate,
            )
            await communicate.save(output_path)
            logger.info("TTS saved: {} ({} chars)", output_path, len(text))
            return output_path
        except Exception as e:
            logger.error("TTS failed: {}", e)
            return None

    def speak_sync(self, text: str, output_path: str | None = None) -> str | None:
        \"\"\"Synchronous wrapper for speak().\"\"\"
        return asyncio.run(self.speak(text, output_path))
