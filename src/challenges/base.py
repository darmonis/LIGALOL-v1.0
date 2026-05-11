"""Base class for the challenge system in LIGALOL.

All challenges must inherit from Challenge and implement the evaluate method.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

import pandas as pd


class Challenge(ABC):
    """Abstract base class for a challenge/title.

    Attributes:
        name: The display name of the challenge.
        description: A short description of what the challenge measures.
        category: Either 'daily' or 'weekly'.
    """

    def __init__(self, name: str, description: str, category: str):
        self.name = name
        self.description = description
        self.category = category  # "daily" or "weekly"

    @abstractmethod
    def evaluate(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        """Evaluate the challenge against the provided DataFrame.

        Args:
            df: DataFrame containing match statistics.

        Returns:
            List of result dicts with keys:
                - player (str): game_name
                - value (Any): the measured metric
                - achieved (bool): whether the player achieved the challenge
        """
        ...

    def _build_result(
        self, player: str, value: Any, achieved: bool
    ) -> dict[str, Any]:
        """Build a standardized result dict."""
        return {
            "challenge_name": self.name,
            "challenge_description": self.description,
            "player": player,
            "value": value,
            "achieved": achieved,
            "timestamp": datetime.now(),
        }
