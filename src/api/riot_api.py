"""Riot Games API client for LIGALOL.

Provides functions to interact with Riot's account-v1 and match-v5 APIs.
Handles rate limiting, retries, and error management.
"""

import time
from datetime import datetime, timedelta
from typing import Any

import requests

from ..config_loader import load_config

# Base URLs for Riot APIs
ACCOUNT_API_URL = "https://europe.api.riotgames.com/riot/account/v1"
MATCH_API_URL = "https://europe.api.riotgames.com/lol/match/v5"

# Queue IDs for SoloQ and FlexQ
SOLOQ_QUEUE_ID = 420
FLEXQ_QUEUE_ID = 440
VALID_QUEUE_IDS = {SOLOQ_QUEUE_ID, FLEXQ_QUEUE_ID}


def _get_headers() -> dict[str, str]:
    """Return headers with the API key."""
    config = load_config()
    return {"X-Riot-Token": config["api_key"]}


def _make_request(url: str, max_retries: int = 3) -> dict[str, Any] | None:
    """Make a GET request with rate limit handling and retries.

    Args:
        url: The URL to request.
        max_retries: Maximum number of retries on rate limit.

    Returns:
        JSON response as dict, or None if the request fails.
    """
    headers = _get_headers()
    retries = 0

    while retries <= max_retries:
        try:
            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 1))
                time.sleep(retry_after)
                retries += 1
                continue

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"Request error for {url}: {e}")
            return None

    print(f"Max retries exceeded for {url}")
    return None


def get_puuid(game_name: str, tag_line: str) -> str | None:
    """Resolve a PUUID from a Riot ID (gameName + tagLine).

    Args:
        game_name: The player's game name.
        tag_line: The player's tagline (e.g., EUW, NA1).

    Returns:
        The player's PUUID string, or None if not found.
    """
    url = f"{ACCOUNT_API_URL}/accounts/by-riot-id/{game_name}/{tag_line}"
    data = _make_request(url)
    return data.get("puuid") if data else None


def get_match_ids(
    puuid: str,
    start_time: int | None = None,
    end_time: int | None = None,
    queue_ids: list[int] | None = None,
    count: int = 100,
) -> list[str]:
    """Fetch match IDs for a player from match-v5.

    Args:
        puuid: The player's PUUID.
        start_time: Start time as Unix epoch (seconds). Defaults to 24h ago.
        end_time: End time as Unix epoch (seconds). Defaults to now.
        queue_ids: List of queue IDs to filter. Defaults to [420, 440].
        count: Number of matches to retrieve (max 100).

    Returns:
        List of match ID strings.
    """
    if start_time is None:
        start_time = int((datetime.now() - timedelta(hours=24)).timestamp())
    if end_time is None:
        end_time = int(datetime.now().timestamp())
    if queue_ids is None:
        queue_ids = list(VALID_QUEUE_IDS)

    all_match_ids: list[str] = []

    for queue_id in queue_ids:
        url = (
            f"{MATCH_API_URL}/matches/by-puuid/{puuid}/ids"
            f"?queue={queue_id}"
            f"&startTime={start_time}"
            f"&endTime={end_time}"
            f"&start=0"
            f"&count={count}"
        )
        data = _make_request(url)
        if data and isinstance(data, list):
            all_match_ids.extend(data)

    # Remove duplicates while preserving order
    seen = set()
    unique_match_ids = []
    for m_id in all_match_ids:
        if m_id not in seen:
            seen.add(m_id)
            unique_match_ids.append(m_id)

    return unique_match_ids


def get_match_details(match_id: str) -> dict[str, Any] | None:
    """Fetch detailed match data from match-v5.

    Args:
        match_id: The match ID.

    Returns:
        Match details JSON as dict, or None if not found.
    """
    url = f"{MATCH_API_URL}/matches/{match_id}"
    return _make_request(url)


def fetch_player_matches(
    player: dict[str, str],
    hours: int = 24,
) -> list[dict[str, Any]]:
    """Fetch all match details for a player in the last N hours.

    Args:
        player: Dict with keys 'game_name' and 'tag_line'.
        hours: Number of hours to look back.

    Returns:
        List of match detail dicts.
    """
    game_name = player.get("game_name")
    tag_line = player.get("tag_line")

    if not game_name or not tag_line:
        print(f"Invalid player data: {player}")
        return []

    puuid = get_puuid(game_name, tag_line)
    if not puuid:
        print(f"Could not resolve PUUID for {game_name}#{tag_line}")
        return []

    start_time = int((datetime.now() - timedelta(hours=hours)).timestamp())
    end_time = int(datetime.now().timestamp())

    match_ids = get_match_ids(
        puuid=puuid,
        start_time=start_time,
        end_time=end_time,
        queue_ids=list(VALID_QUEUE_IDS),
    )

    matches: list[dict[str, Any]] = []
    for match_id in match_ids:
        details = get_match_details(match_id)
        if details:
            # Store the player's PUUID in the match data for later reference
            details["_query_puuid"] = puuid
            details["_query_game_name"] = game_name
            details["_query_tag_line"] = tag_line
            matches.append(details)

    return matches
