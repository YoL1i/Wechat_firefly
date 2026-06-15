\"\"\"WeChat bridge - wraps WeChatFerry for message send/receive.\"\"\"

from __future__ import annotations

from typing import Any, Callable

from loguru import logger

from wchat.bridge.message import WeChatMessage, MessageType, MessageDirection
from wchat.config.loader import config


class WeChatBridge:
    \"\"\"Interface to WeChat via WeChatFerry.\"\"\"

    def __init__(self):
        self._wcf = None
        self._connected = False
        self._message_handler: Callable | None = None

    def connect(self) -> bool:
        \"\"\"Connect to WeChatFerry.\"\"\"
        try:
            import wcf
            host = config.get("wechat", "host", default="127.0.0.1")
            port = int(config.get("wechat", "port", default=10080))
            self._wcf = wcf.Wcf(host=host, port=port)
            self._connected = True
            logger.info("Connected to WeChatFerry")
            return True
        except Exception as e:
            logger.error("Failed to connect to WeChatFerry: {}", e)
            self._connected = False
            return False

    @property
    def connected(self) -> bool:
        return self._connected

    def on_message(self, handler: Callable) -> None:
        \"\"\"Register a handler for incoming messages.\"\"\"
        self._message_handler = handler

    def send_text(self, receiver: str, text: str, is_group: bool = False) -> bool:
        \"\"\"Send a text message.\"\"\"
        if not self._connected or not self._wcf:
            logger.warning("Cannot send message: not connected")
            return False
        try:
            if is_group:
                self._wcf.send_text(text, receiver)
            else:
                self._wcf.send_text(text, receiver)
            logger.debug("Sent text to {}: {}...", receiver, text[:30])
            return True
        except Exception as e:
            logger.error("Failed to send text: {}", e)
            return False

    def send_voice(self, receiver: str, file_path: str) -> bool:
        \"\"\"Send a voice message.\"\"\"
        if not self._connected or not self._wcf:
            logger.warning("Cannot send voice: not connected")
            return False
        try:
            self._wcf.send_voice(receiver, file_path)
            logger.debug("Sent voice to {}: {}", receiver, file_path)
            return True
        except Exception as e:
            logger.error("Failed to send voice: {}", e)
            return False

    def _normalize_message(self, raw_msg: Any) -> WeChatMessage | None:
        \"\"\"Convert a raw WeChatFerry message to our model.\"\"\"
        try:
            msg_type = MessageType(raw_msg.type)
        except ValueError:
            msg_type = MessageType.UNKNOWN

        return WeChatMessage(
            msg_id=getattr(raw_msg, "id", 0),
            msg_type=msg_type,
            content=getattr(raw_msg, "content", "") or "",
            sender=getattr(raw_msg, "sender", ""),
            room_id=getattr(raw_msg, "roomid", None),
            is_self=getattr(raw_msg, "is_self", False),
            is_group=bool(getattr(raw_msg, "roomid", None)),
        )

    def start_listening(self) -> None:
        \"\"\"Start the message listening loop.\"\"\"
        if not self._connected or not self._wcf:
            logger.error("Cannot start listening: not connected")
            return

        logger.info("Listening for WeChat messages...")
        self._wcf.on_recv_message(self._on_raw_message)

    def _on_raw_message(self, raw_msg: Any) -> None:
        msg = self._normalize_message(raw_msg)
        if msg and self._message_handler:
            self._message_handler(msg)

    def get_self_wxid(self) -> str:
        if self._wcf:
            return self._wcf.get_self_wxid()
        return ""

    def get_contacts(self) -> list[dict]:
        if self._wcf:
            return self._wcf.get_contacts()
        return []

    def disconnect(self) -> None:
        if self._wcf:
            try:
                self._wcf.cleanup()
            except Exception:
                pass
        self._connected = False
        logger.info("Disconnected from WeChatFerry")
