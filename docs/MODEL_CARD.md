# Model card: first-basket baseline

## Intended use

Research and rank first-basket offers from a complete event market. The output is a probability,
expected return, capped fractional-Kelly stake, decision reason, and immutable model version.

## Learning policy

Settled predictions belong in an append-only ledger. Retraining is scheduled and chronological;
a challenger is promoted only after reproducible walk-forward gains. A single loss is evidence,
not an instruction. No outcome or closing price may enter features for an earlier prediction.

## Promotion gates

- Beat the current champion on out-of-sample log loss and Brier score.
- Remain calibrated by probability and odds band with useful confidence intervals.
- Show positive CLV after realistic latency; report ROI with uncertainty and maximum drawdown.
- Pass schema, timestamp, duplicate-event, missing-lineup, and odds-staleness checks.
- Survive season/team holdouts and sensitivity tests for scratches and opening-tip assumptions.

## Known limitations

The baseline has no lineup, tip, possession, play-call, or sportsbook-specific features. Proportional
vig removal is simplistic for long-shot markets, isotonic estimates need substantial validation
data, and offered outcomes must be complete. Historical backtests do not establish future profit.
Kelly sizing is highly sensitive to probability error, so the implementation caps exposure.

## Operational safeguards

Pin data and code versions, retain raw snapshots, use event-time joins, monitor drift without
automatic promotion, support rollback, and stop recommendations when required feeds are stale.
