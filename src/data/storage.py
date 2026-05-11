"""Data storage module for LIGALOL.

Handles persistent storage of match statistics in CSV format.
Provides functions for querying daily and weekly stats.
"""

import os
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

CSV_PATH = Path(__file__).parent.parent.parent / "data" / "matches_history.csv"


def _ensure_csv_exists() -> None:
    """Create the CSV file with headers if it doesn't exist."""
    if not CSV_PATH.exists():
        CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
        df = pd.DataFrame(columns=[
            "puuid", "game_name", "tag_line", "match_id", "timestamp",
            "kills", "deaths", "assists", "kda", "total_damage",
            "first_blood", "first_blood_assist", "turret_kills",
            "wards_placed", "wards_killed", "vision_score",
            "cs", "cs_per_min", "gold_earned", "game_duration", "win",
        ])
        df.to_csv(CSV_PATH, index=False)


def save_match_data(player_stats_list: list[dict[str, Any]]) -> None:
    """Save or update match data in the historical CSV.

    Performs an upsert based on puuid + match_id to avoid duplicates.

    Args:
        player_stats_list: List of stat dicts from extract_player_stats.
    """
    _ensure_csv_exists()
    if not player_stats_list:
        return

    existing_df = pd.read_csv(CSV_PATH, parse_dates=["timestamp"])
    new_df = pd.DataFrame(player_stats_list)

    # Ensure timestamp is datetime
    if not pd.api.types.is_datetime64_any_dtype(new_df["timestamp"]):
        new_df["timestamp"] = pd.to_datetime(new_df["timestamp"])

    # Remove duplicates: if (puuid, match_id) already exists, drop from new_df
    if not existing_df.empty:
        existing_keys = set(zip(existing_df["puuid"], existing_df["match_id"]))
        new_df = new_df[
            ~new_df.apply(lambda row: (row["puuid"], row["match_id"]) in existing_keys, axis=1)
        ]

    if not new_df.empty:
        combined = pd.concat([existing_df, new_df], ignore_index=True)
        combined.to_csv(CSV_PATH, index=False)


def get_all_stats() -> pd.DataFrame:
    """Load all historical match statistics.

    Returns:
        DataFrame with all stored match data.
    """
    _ensure_csv_exists()
    df = pd.read_csv(CSV_PATH, parse_dates=["timestamp"])
    return df


def get_daily_stats(query_date: date | None = None) -> pd.DataFrame:
    """Get statistics for a specific day.

    Args:
        query_date: The date to query. Defaults to today.

    Returns:
        DataFrame filtered to the specified date.
    """
    if query_date is None:
        query_date = datetime.now().date()

    df = get_all_stats()
    if df.empty:
        return df

    df["date"] = df["timestamp"].dt.date
    filtered = df.loc[df["date"] == query_date].copy()
    filtered.drop(columns=["date"], inplace=True)
    return filtered


def get_weekly_stats() -> pd.DataFrame:
    """Get statistics for the last 7 days.

    Returns:
        DataFrame filtered to the last 7 days.
    """
    df = get_all_stats()
    if df.empty:
        return df

    cutoff = datetime.now() - timedelta(days=7)
    filtered = df.loc[df["timestamp"] >= cutoff].copy()
    return filtered
