# PickIt

PickIt is a leakage-resistant research baseline for **NBA/WNBA first-basket bets**. It turns
historical player/market observations into calibrated probabilities, prices the sportsbook
offer after removing vig, records every decision, and only learns during explicit retraining.

> **Responsible use:** no model guarantees profit. Long-shot bets have severe variance. Set
> limits, never chase losses, and follow local laws. This project is research software—not
> financial advice.

## What is included

- Empirical-Bayes player probabilities with recency weighting and sample-size shrinkage.
- A market prior with proportional vig removal.
- An ensemble whose market/model weight is selected using chronological validation.
- Isotonic probability calibration fitted without future leakage.
- EV, fractional-Kelly sizing, minimum-edge gates, and auditable recommendation reasons.
- An append-only prediction ledger, settlement, Brier/log-loss/ROI/CLV reporting, and drift
  checks. Losing one bet never triggers an unsafe online update.
- Walk-forward evaluation and model artifact versioning using only the Python standard library.

This is a strong **foundation**, not a claim of a production edge. Real deployment requires
licensed, timestamped play-by-play, lineup, injury, tip, and odds feeds. Never evaluate against
odds that were unavailable when the pick was made.

## Quick start

Requires Python 3.11+.

```bash
python -m unittest discover -s tests -v
python -m pickit demo
```

## Input model

Each historical row is an `Observation`: game time, player, binary first-scorer outcome,
pre-pick decimal odds, and optional context tags. For each event, provide **all offered
outcomes** so vig removal is meaningful. Training data must already reflect the information
available at its `observed_at` timestamp.

```python
from datetime import datetime, timezone
from pickit import FirstBasketModel, Observation, Offer

model = FirstBasketModel()
model.fit(history, cutoff=datetime(2026, 1, 1, tzinfo=timezone.utc))
quote = model.quote([
    Offer("p1", 13.0), Offer("p2", 15.0), Offer("p3", 19.0)
], as_of=datetime.now(timezone.utc))
print(quote[0])
```

## Production roadmap

1. Store immutable odds snapshots and source timestamps in PostgreSQL.
2. Add tip-win, first-possession, lineup, first-shot, play-call, and shot-conversion submodels.
3. Compare CatBoost/LightGBM and hierarchical Bayesian candidates via season-by-season
   walk-forward evaluation; promote only models that improve calibration and CLV out of sample.
4. Schedule controlled retraining, registry promotion/rollback, and feature/data-quality tests.
5. Serve signed model versions through an API and monitor calibration by league, sportsbook,
   price band, team, season, and data latency.

See [`docs/MODEL_CARD.md`](docs/MODEL_CARD.md) for assumptions, failure modes, and promotion
criteria.
