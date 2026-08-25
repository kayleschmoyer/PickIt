from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from .types import Quote


@dataclass(frozen=True)
class LedgerEntry:
    kind: str
    event_id: str
    player_id: str
    recorded_at: str
    payload: dict[str, object]


class PredictionLedger:
    """Append-only JSONL audit trail; settlement never mutates a prediction."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def record_prediction(self, event_id: str, quote: Quote, recorded_at: datetime) -> None:
        self._validate_time(recorded_at)
        self._append(LedgerEntry("prediction", event_id, quote.player_id, recorded_at.isoformat(), asdict(quote)))

    def record_settlement(self, event_id: str, player_id: str, won: bool, settled_at: datetime) -> None:
        self._validate_time(settled_at)
        self._append(LedgerEntry("settlement", event_id, player_id, settled_at.isoformat(), {"won": won}))

    def read(self) -> list[LedgerEntry]:
        if not self.path.exists():
            return []
        return [LedgerEntry(**json.loads(line)) for line in self.path.read_text(encoding="utf-8").splitlines()]

    def _append(self, entry: LedgerEntry) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(asdict(entry), sort_keys=True, separators=(",", ":")) + "\n")

    @staticmethod
    def _validate_time(value: datetime) -> None:
        if value.tzinfo is None:
            raise ValueError("ledger timestamps must be timezone-aware")
