"""Challenge definitions for LIGALOL.

Implements all default challenges. To add a new challenge, create a new class
inheriting from Challenge and implement the evaluate method.
"""

from typing import Any

import pandas as pd

from .base import Challenge


class ReyDelFarm(Challenge):
    """Best CS per minute in a single day."""

    def __init__(self):
        super().__init__(
            name="Rey del Farm",
            description="Mayor CS/min en una partida del día",
            category="daily",
        )

    def evaluate(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        if df.empty:
            return []
        # Find max cs_per_min per player, then the overall max
        best_per_player = df.groupby("game_name")["cs_per_min"].max().reset_index()
        overall_max = best_per_player["cs_per_min"].max()
        winners = best_per_player[best_per_player["cs_per_min"] == overall_max]

        results = []
        for _, row in winners.iterrows():
            results.append(self._build_result(
                player=row["game_name"],
                value=round(row["cs_per_min"], 2),
                achieved=True,
            ))
        return results


class FuenteDeOro(Challenge):
    """Most deaths in a single day (ironic title)."""

    def __init__(self):
        super().__init__(
            name="La Fuente de Oro",
            description="Más muertes en una partida del día",
            category="daily",
        )

    def evaluate(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        if df.empty:
            return []
        max_deaths = df.groupby("game_name")["deaths"].max().reset_index()
        overall_max = max_deaths["deaths"].max()
        winners = max_deaths[max_deaths["deaths"] == overall_max]

        results = []
        for _, row in winners.iterrows():
            results.append(self._build_result(
                player=row["game_name"],
                value=int(row["deaths"]),
                achieved=True,
            ))
        return results


class ElCentinela(Challenge):
    """Best vision score in a single day."""

    def __init__(self):
        super().__init__(
            name="El Centinela",
            description="Mayor puntuación de visión en una partida del día",
            category="daily",
        )

    def evaluate(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        if df.empty:
            return []
        best_vision = df.groupby("game_name")["vision_score"].max().reset_index()
        overall_max = best_vision["vision_score"].max()
        winners = best_vision[best_vision["vision_score"] == overall_max]

        results = []
        for _, row in winners.iterrows():
            results.append(self._build_result(
                player=row["game_name"],
                value=int(row["vision_score"]),
                achieved=True,
            ))
        return results


class MVP_Del_Dia(Challenge):
    """Best KDA in a single day."""

    def __init__(self):
        super().__init__(
            name="MVP del Día",
            description="Mejor KDA en una partida del día",
            category="daily",
        )

    def evaluate(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        if df.empty:
            return []
        best_kda = df.groupby("game_name")["kda"].max().reset_index()
        overall_max = best_kda["kda"].max()
        winners = best_kda[best_kda["kda"] == overall_max]

        results = []
        for _, row in winners.iterrows():
            results.append(self._build_result(
                player=row["game_name"],
                value=round(row["kda"], 2),
                achieved=True,
            ))
        return results


class Fedeador_Del_Dia(Challenge):
    """Worst KDA in a single day."""

    def __init__(self):
        super().__init__(
            name="Fedeador del Día",
            description="Peor KDA en una partida del día",
            category="daily",
        )

    def evaluate(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        if df.empty:
            return []
        worst_kda = df.groupby("game_name")["kda"].min().reset_index()
        overall_min = worst_kda["kda"].min()
        winners = worst_kda[worst_kda["kda"] == overall_min]

        results = []
        for _, row in winners.iterrows():
            results.append(self._build_result(
                player=row["game_name"],
                value=round(row["kda"], 2),
                achieved=True,
            ))
        return results


class FabricaDeDano(Challenge):
    """Accumulate 80k+ damage in the last 5 matches."""

    def __init__(self):
        super().__init__(
            name="Fábrica de Daño",
            description="Acumular +80k de daño en las últimas 5 partidas",
            category="weekly",
        )

    def evaluate(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        if df.empty:
            return []
        # Sort by timestamp desc, take last 5 per player, sum damage
        df_sorted = df.sort_values("timestamp", ascending=False)
        results = []

        for player, group in df_sorted.groupby("game_name"):
            last_5 = group.head(5)
            total_damage = last_5["total_damage"].sum()
            achieved = total_damage >= 80000
            results.append(self._build_result(
                player=player,
                value=int(total_damage),
                achieved=achieved,
            ))

        return results


class AdictoALaSangre(Challenge):
    """Highest first blood percentage in the week."""

    def __init__(self):
        super().__init__(
            name="Adicto a la Sangre",
            description="Mayor % de primeras sangres en la semana",
            category="weekly",
        )

    def evaluate(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        if df.empty:
            return []
        # Calculate first blood percentage per player
        stats = df.groupby("game_name").agg(
            first_bloods=("first_blood", "sum"),
            total_games=("first_blood", "count"),
        ).reset_index()
        stats["fb_pct"] = stats["first_bloods"] / stats["total_games"] * 100
        overall_max = stats["fb_pct"].max()
        winners = stats[stats["fb_pct"] == overall_max]

        results = []
        for _, row in winners.iterrows():
            results.append(self._build_result(
                player=row["game_name"],
                value=f"{row['fb_pct']:.1f}%",
                achieved=True,
            ))
        return results
