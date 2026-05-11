"""Data processing module for LIGALOL.

Extracts raw metrics from Riot match-v5 responses.
"""

from datetime import datetime
from typing import Any


def extract_player_stats(
    match_details: dict[str, Any],
    puuid: str,
    game_name: str,
    tag_line: str,
) -> dict[str, Any] | None:
    """Extract player statistics from a match-v5 response.

    Args:
        match_details: Raw match data from match-v5 API.
        puuid: The player's PUUID.
        game_name: The player's game name.
        tag_line: The player's tagline.

    Returns:
        Dict with extracted metrics, or None if player not found in match.
    """
    info = match_details.get("info", {})
    metadata = match_details.get("metadata", {})
    participants = info.get("participants", [])

    # Find the participant matching the PUUID
    player_data = None
    for participant in participants:
        if participant.get("puuid") == puuid:
            player_data = participant
            break

    if player_data is None:
        return None

    game_duration = info.get("gameDuration", 0)
    if game_duration == 0:
        game_duration = info.get("gameDuration", 0)

    kills = player_data.get("kills", 0)
    deaths = player_data.get("deaths", 0)
    assists = player_data.get("assists", 0)
    kda = (kills + assists) / max(deaths, 1)

    cs = player_data.get("totalMinionsKilled", 0)
    cs_per_min = cs / max(game_duration / 60, 1)

    timestamp_ms = info.get("gameCreation", 0)
    timestamp = datetime.fromtimestamp(timestamp_ms / 1000) if timestamp_ms else datetime.now()

    return {
        "puuid": puuid,
        "game_name": game_name,
        "tag_line": tag_line,
        "match_id": metadata.get("matchId", ""),
        "timestamp": timestamp,
        "kills": kills,
        "deaths": deaths,
        "assists": assists,
        "kda": round(kda, 2),
        "total_damage": player_data.get("totalDamageDealtToChampions", 0),
        "first_blood": bool(player_data.get("firstBloodKill", False)),
        "first_blood_assist": bool(player_data.get("firstBloodAssist", False)),
        "turret_kills": player_data.get("turretKills", 0),
        "wards_placed": player_data.get("wardsPlaced", 0),
        "wards_killed": player_data.get("wardsKilled", 0),
        "vision_score": player_data.get("visionScore", 0),
        "cs": cs,
        "cs_per_min": round(cs_per_min, 2),
        "gold_earned": player_data.get("goldEarned", 0),
        "game_duration": game_duration,
        "win": bool(player_data.get("win", False)),
    }
