"""Configuration loader for LIGALOL project.

Loads player data from players.json and environment variables from .env file
or Streamlit secrets when running on Streamlit Cloud.
"""

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


def _get_config_dir() -> Path:
    """Return the config directory path."""
    return Path(__file__).parent.parent / "config"


def _get_secret(key: str, default: str | None = None) -> str | None:
    """Try to get a secret from environment or Streamlit secrets."""
    # 1. Check standard environment variables
    value = os.getenv(key)
    if value:
        return value

    # 2. Check Streamlit secrets (for Streamlit Cloud deployment)
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key])
    except ImportError:
        pass

    return default


def load_config() -> dict[str, Any]:
    """Load configuration from .env file or environment/Streamlit secrets.

    Returns:
        Dict with API key and settings.
    """
    env_path = _get_config_dir() / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    return {
        "api_key": _get_secret("RIOT_API_KEY", ""),
        "region": _get_secret("REGION", "americas"),
        "default_tagline": _get_secret("DEFAULT_TAGLINE", "EUW"),
        "rate_limit_delay": float(_get_secret("RATE_LIMIT_DELAY", "1.0") or "1.0"),
    }


def load_players() -> list[dict[str, str]]:
    """Load players from players.json.

    Returns:
        List of dicts with keys: game_name, tag_line, puuid (optional).

    Raises:
        FileNotFoundError: If players.json does not exist.
        ValueError: If required fields are missing.
    """
    players_path = _get_config_dir() / "players.json"

    with open(players_path, "r", encoding="utf-8") as f:
        players = json.load(f)

    for i, player in enumerate(players):
        if "game_name" not in player:
            raise ValueError(f"Player at index {i} missing 'game_name' field")
        if "tag_line" not in player:
            raise ValueError(f"Player at index {i} missing 'tag_line' field")

    return players