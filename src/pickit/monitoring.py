from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Metrics:
    count: int
    brier: float
    log_loss: float
    roi: float
    clv: float


def score(probabilities: list[float], outcomes: list[bool], odds: list[float], closing_odds: list[float]) -> Metrics:
    lengths = {len(probabilities), len(outcomes), len(odds), len(closing_odds)}
    if lengths != {len(probabilities)} or not probabilities:
        raise ValueError("equal, non-empty series required")
    epsilon = 1e-12
    clipped = [min(1 - epsilon, max(epsilon, p)) for p in probabilities]
    brier = sum((p - y) ** 2 for p, y in zip(clipped, outcomes)) / len(clipped)
    log_loss = -sum(math.log(p if y else 1 - p) for p, y in zip(clipped, outcomes)) / len(clipped)
    profit = sum((price - 1) if won else -1 for price, won in zip(odds, outcomes))
    clv = sum(price / close - 1 for price, close in zip(odds, closing_odds)) / len(odds)
    return Metrics(len(clipped), brier, log_loss, profit / len(odds), clv)


def calibration_drift(reference_brier: float, recent_brier: float, tolerance: float = 0.02) -> bool:
    """Flag degradation for investigation; never silently retrain or promote."""
    return recent_brier - reference_brier > tolerance
