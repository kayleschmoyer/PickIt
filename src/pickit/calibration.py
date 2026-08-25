from __future__ import annotations


class IsotonicCalibrator:
    """Pool-adjacent-violators calibration with deterministic interpolation."""

    def __init__(self) -> None:
        self._blocks: list[tuple[float, float, int]] = []

    def fit(self, probabilities: list[float], outcomes: list[bool]) -> "IsotonicCalibrator":
        if len(probabilities) != len(outcomes) or not probabilities:
            raise ValueError("equal, non-empty probability and outcome lists required")
        blocks: list[list[float]] = []
        for probability, outcome in sorted(zip(probabilities, outcomes)):
            blocks.append([probability, float(outcome), 1.0])
            while len(blocks) >= 2 and blocks[-2][1] / blocks[-2][2] > blocks[-1][1] / blocks[-1][2]:
                right = blocks.pop()
                left = blocks.pop()
                blocks.append([right[0], left[1] + right[1], left[2] + right[2]])
        self._blocks = [(edge, wins / count, int(count)) for edge, wins, count in blocks]
        return self

    def predict(self, probability: float) -> float:
        if not self._blocks:
            return min(1.0, max(0.0, probability))
        for edge, value, _ in self._blocks:
            if probability <= edge:
                return value
        return self._blocks[-1][1]
