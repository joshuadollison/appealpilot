"""Local keys loader.

Loads API keys from a local config file that is intentionally gitignored.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping

DEFAULT_KEYS_PATH = Path(__file__).resolve().parent / "keys.local.yaml"


def _read_yaml(path: Path) -> Mapping[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError(
            "PyYAML is required to load local keys config."
        ) from exc

    data = yaml.safe_load(path.read_text()) or {}
    if not isinstance(data, dict):
        return {}
    return data


def load_local_keys(path: Path | None = None, override_env: bool = False) -> dict[str, bool]:
    """Load local API keys into environment variables.

    Accepted schema:
    - openai_api_key: "..."
      groq_api_key: "..."
    - keys:
        openai_api_key: "..."
        groq_api_key: "..."
    """

    keys_path = path or Path(os.getenv("APPEALPILOT_KEYS_PATH", str(DEFAULT_KEYS_PATH)))
    if not keys_path.exists():
        return {
            "loaded": False,
            "path_exists": False,
            "openai": bool(os.getenv("OPENAI_API_KEY")),
            "groq": bool(os.getenv("GROQ_API_KEY")),
        }

    payload = _read_yaml(keys_path)
    keys_section = payload.get("keys", payload)
    if not isinstance(keys_section, Mapping):
        keys_section = {}

    openai_key = str(keys_section.get("openai_api_key", "")).strip()
    groq_key = str(keys_section.get("groq_api_key", "")).strip()

    if openai_key and (override_env or not os.getenv("OPENAI_API_KEY")):
        os.environ["OPENAI_API_KEY"] = openai_key
    if groq_key and (override_env or not os.getenv("GROQ_API_KEY")):
        os.environ["GROQ_API_KEY"] = groq_key

    return {
        "loaded": bool(openai_key or groq_key),
        "path_exists": True,
        "openai": bool(os.getenv("OPENAI_API_KEY")),
        "groq": bool(os.getenv("GROQ_API_KEY")),
    }
