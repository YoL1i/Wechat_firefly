import json
import os
from pathlib import Path
from typing import Any

import yaml
from loguru import logger


class Config:
    \"\"\"Global configuration loader.\"\"\"

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._loaded = False
        return cls._instance

    def load(self, config_dir: str | Path | None = None) -> None:
        if self._loaded:
            return

        if config_dir is None:
            config_dir = Path(__file__).parent.parent.parent / "config"
        self.config_dir = Path(config_dir)

        # Load main config
        config_file = self.config_dir / "config.yaml"
        if config_file.exists():
            with open(config_file, encoding="utf-8") as f:
                self.data: dict[str, Any] = yaml.safe_load(f) or {}
        else:
            self.data = {}
            logger.warning("config.yaml not found at {}", config_file)

        # Override with env vars
        self._apply_env_overrides()
        self._loaded = True
        logger.info("Configuration loaded from {}", config_file)

    def _apply_env_overrides(self) -> None:
        env_map = {
            "DEEPSEEK_API_KEY": ("llm", "deepseek_api_key"),
            "OPENAI_API_KEY": ("llm", "openai_api_key"),
            "DEFAULT_LLM": ("llm", "default"),
            "WCF_HOST": ("wechat", "host"),
            "WCF_PORT": ("wechat", "port"),
            "SERVER_MODE": ("server", "enabled"),
            "SERVER_HOST": ("server", "host"),
            "SERVER_PORT": ("server", "port"),
        }
        for env_key, config_path in env_map.items():
            value = os.getenv(env_key)
            if value is not None:
                section = self.data.setdefault(config_path[0], {})
                section[config_path[1]] = value

    def get(self, *keys: str, default: Any = None) -> Any:
        \"\"\"Get a nested config value by keys. e.g. config.get('llm', 'default')\"\"\"
        if not self._loaded:
            self.load()
        current = self.data
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
                if current is None:
                    return default
            else:
                return default
        return current

    def get_character_path(self, name: str) -> Path:
        return self.config_dir / "characters" / f"{name}.json"

    def load_character_card(self, name: str) -> dict[str, Any]:
        path = self.get_character_path(name)
        if not path.exists():
            logger.error("Character card not found: {}", path)
            return {}
        with open(path, encoding="utf-8") as f:
            return json.load(f)


# Global singleton
config = Config()
