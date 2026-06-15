\"\"\"Utility functions.\"\"\"

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def ensure_dir(path: str | Path) -> Path:
    \"\"\"Ensure a directory exists.\"\"\"
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def load_json(path: str | Path) -> dict[str, Any]:
    \"\"\"Load a JSON file.\"\"\"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def truncate(text: str, max_len: int = 50) -> str:
    \"\"\"Truncate text for display.\"\"\"
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."
