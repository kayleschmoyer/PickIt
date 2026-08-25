import unittest
import tempfile
from datetime import datetime, timedelta, timezone

from pickit import FirstBasketModel, Observation, Offer, PredictionLedger
from pickit.model import remove_vig
from pickit.monitoring import calibration_drift, score


class ModelTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.rows = [
            Observation(str(game), self.now - timedelta(days=20 - game), player, player == "a" and game % 3 == 0, odds)
            for game in range(15)
            for player, odds in (("a", 8.0), ("b", 12.0), ("c", 15.0))
        ]

    def test_vig_is_removed(self):
        fair = remove_vig([Offer("a", 2), Offer("b", 2)])
        self.assertEqual(fair, {"a": 0.5, "b": 0.5})

    def test_fit_excludes_future_and_quotes_sum_to_one(self):
        future = Observation("future", self.now + timedelta(days=1), "a", True, 8)
        model = FirstBasketModel().fit(self.rows + [future], self.now)
        quotes = model.quote([Offer("a", 8), Offer("b", 12), Offer("c", 15)], self.now)
        self.assertAlmostEqual(sum(q.probability for q in quotes), 1)
        self.assertTrue(all(0 <= q.stake_fraction <= 0.01 for q in quotes))

    def test_monitoring_metrics_and_drift(self):
        metrics = score([0.8, 0.2], [True, False], [2, 2], [1.8, 2.2])
        self.assertAlmostEqual(metrics.brier, 0.04)
        self.assertTrue(calibration_drift(0.04, 0.07))

    def test_naive_timestamps_rejected(self):
        with self.assertRaises(ValueError):
            Observation("x", datetime.now(), "a", False, 2)

    def test_ledger_appends_prediction_and_settlement(self):
        model = FirstBasketModel().fit(self.rows, self.now)
        quote = model.quote([Offer("a", 8), Offer("b", 12)], self.now)[0]
        with tempfile.TemporaryDirectory() as directory:
            ledger = PredictionLedger(f"{directory}/ledger.jsonl")
            ledger.record_prediction("game", quote, self.now)
            ledger.record_settlement("game", quote.player_id, False, self.now + timedelta(hours=3))
            entries = ledger.read()
        self.assertEqual([entry.kind for entry in entries], ["prediction", "settlement"])
        self.assertEqual(entries[0].payload["model_version"], model.version)


if __name__ == "__main__":
    unittest.main()
