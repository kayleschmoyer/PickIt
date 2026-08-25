from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from datetime import datetime

from .calibration import IsotonicCalibrator
from .types import Observation, Offer, Quote


def remove_vig(offers: list[Offer]) -> dict[str, float]:
    raw = {offer.player_id: 1 / offer.decimal_odds for offer in offers}
    total = sum(raw.values())
    if not raw or total <= 0:
        raise ValueError("at least one valid offer is required")
    return {player: probability / total for player, probability in raw.items()}


class FirstBasketModel:
    """Recency-weighted empirical Bayes baseline blended with the betting market."""

    def __init__(self, half_life_days: float = 120, prior_strength: float = 25) -> None:
        if half_life_days <= 0 or prior_strength <= 0:
            raise ValueError("half_life_days and prior_strength must be positive")
        self.half_life_days = half_life_days
        self.prior_strength = prior_strength
        self.player_rates: dict[str, float] = {}
        self.market_weight = 0.5
        self.calibrator = IsotonicCalibrator()
        self.version = "unfitted"

    def fit(self, observations: list[Observation], cutoff: datetime) -> "FirstBasketModel":
        if cutoff.tzinfo is None:
            raise ValueError("cutoff must be timezone-aware")
        rows = sorted((row for row in observations if row.observed_at < cutoff), key=lambda row: row.observed_at)
        if not rows:
            raise ValueError("no observations exist before cutoff")
        # Reserve the newest 20% for chronological tuning/calibration.
        split = max(1, int(len(rows) * 0.8))
        train, validation = rows[:split], rows[split:]
        if not validation:
            validation = train
        event_sizes: dict[str, int] = defaultdict(int)
        for row in train:
            event_sizes[row.event_id] += 1
        base = sum(1 / size for size in event_sizes.values()) / len(event_sizes)
        wins: dict[str, float] = defaultdict(float)
        exposure: dict[str, float] = defaultdict(float)
        for row in train:
            age = max(0.0, (cutoff - row.observed_at).total_seconds() / 86400)
            weight = 0.5 ** (age / self.half_life_days)
            exposure[row.player_id] += weight
            wins[row.player_id] += weight * row.won
        self.player_rates = {
            player: (wins[player] + self.prior_strength * base) / (count + self.prior_strength)
            for player, count in exposure.items()
        }
        candidates = [i / 10 for i in range(2, 9)]
        self.market_weight = min(candidates, key=lambda weight: self._validation_loss(validation, weight))
        raw = [self._blend(row.player_id, 1 / row.decimal_odds, self.market_weight) for row in validation]
        self.calibrator.fit(raw, [row.won for row in validation])
        fingerprint = json.dumps([(r.event_id, r.player_id, r.won) for r in rows], separators=(",", ":"))
        self.version = hashlib.sha256(fingerprint.encode()).hexdigest()[:12]
        return self

    def _blend(self, player: str, market: float, market_weight: float) -> float:
        rate = self.player_rates.get(player, market)
        return market_weight * market + (1 - market_weight) * rate

    def _validation_loss(self, rows: list[Observation], weight: float) -> float:
        epsilon = 1e-12
        loss = 0.0
        for row in rows:
            p = min(1 - epsilon, max(epsilon, self._blend(row.player_id, 1 / row.decimal_odds, weight)))
            loss -= math.log(p if row.won else 1 - p)
        return loss / len(rows)

    def quote(
        self,
        offers: list[Offer],
        as_of: datetime,
        *,
        min_edge: float = 0.015,
        kelly_fraction: float = 0.25,
        max_stake: float = 0.01,
    ) -> list[Quote]:
        if self.version == "unfitted":
            raise RuntimeError("fit the model before requesting quotes")
        if as_of.tzinfo is None:
            raise ValueError("as_of must be timezone-aware")
        fair = remove_vig(offers)
        raw = {offer.player_id: self._blend(offer.player_id, fair[offer.player_id], self.market_weight) for offer in offers}
        calibrated = {player: self.calibrator.predict(probability) for player, probability in raw.items()}
        total = sum(calibrated.values()) or 1
        probabilities = {player: probability / total for player, probability in calibrated.items()}
        quotes = []
        for offer in offers:
            p = probabilities[offer.player_id]
            edge = p - fair[offer.player_id]
            ev = p * offer.decimal_odds - 1
            full_kelly = max(0.0, (p * offer.decimal_odds - 1) / (offer.decimal_odds - 1))
            bet = edge >= min_edge and ev > 0
            quotes.append(Quote(offer.player_id, p, fair[offer.player_id], offer.decimal_odds, ev,
                                min(max_stake, full_kelly * kelly_fraction) if bet else 0.0, bet,
                                "edge and EV gates passed" if bet else "insufficient calibrated edge",
                                self.version))
        return sorted(quotes, key=lambda quote: quote.expected_value, reverse=True)
