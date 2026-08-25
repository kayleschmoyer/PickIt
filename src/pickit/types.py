from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class Observation:
    event_id: str
    observed_at: datetime
    player_id: str
    won: bool
    decimal_odds: float
    context: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.observed_at.tzinfo is None:
            raise ValueError("observed_at must be timezone-aware")
        if self.decimal_odds <= 1:
            raise ValueError("decimal_odds must be greater than 1")


@dataclass(frozen=True)
class Offer:
    player_id: str
    decimal_odds: float

    def __post_init__(self) -> None:
        if self.decimal_odds <= 1:
            raise ValueError("decimal_odds must be greater than 1")


@dataclass(frozen=True)
class Quote:
    player_id: str
    probability: float
    fair_probability: float
    decimal_odds: float
    expected_value: float
    stake_fraction: float
    bet: bool
    reason: str
    model_version: str
