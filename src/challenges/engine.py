"""Challenge evaluation engine for LIGALOL.

Provides functions to evaluate all registered daily and weekly challenges.
"""

from typing import Any

import pandas as pd

from .base import Challenge
from .definitions import (
    AdictoALaSangre,
    ElCentinela,
    FabricaDeDano,
    Fedeador_Del_Dia,
    FuenteDeOro,
    MVP_Del_Dia,
    ReyDelFarm,
)


def get_all_challenges() -> list[Challenge]:
    """Return instances of all available challenges.

    Returns:
        List of Challenge instances.
    """
    return [
        ReyDelFarm(),
        FuenteDeOro(),
        ElCentinela(),
        MVP_Del_Dia(),
        Fedeador_Del_Dia(),
        FabricaDeDano(),
        AdictoALaSangre(),
    ]


def evaluate_daily_challenges(df_daily: pd.DataFrame) -> list[dict[str, Any]]:
    """Evaluate all daily challenges against the daily DataFrame.

    Args:
        df_daily: DataFrame with daily match stats.

    Returns:
        List of all challenge results.
    """
    challenges = [c for c in get_all_challenges() if c.category == "daily"]
    results: list[dict[str, Any]] = []
    for challenge in challenges:
        results.extend(challenge.evaluate(df_daily))
    return results


def evaluate_weekly_challenges(df_weekly: pd.DataFrame) -> list[dict[str, Any]]:
    """Evaluate all weekly challenges against the weekly DataFrame.

    Args:
        df_weekly: DataFrame with weekly match stats.

    Returns:
        List of all challenge results.
    """
    challenges = [c for c in get_all_challenges() if c.category == "weekly"]
    results: list[dict[str, Any]] = []
    for challenge in challenges:
        results.extend(challenge.evaluate(df_weekly))
    return results
