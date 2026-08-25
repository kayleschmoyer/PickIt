from datetime import datetime, timedelta, timezone

from .model import FirstBasketModel
from .types import Observation, Offer


def main() -> None:
    now = datetime.now(timezone.utc)
    history = []
    for game in range(30):
        for player, odds in (("alpha", 10.0), ("beta", 14.0), ("gamma", 18.0)):
            history.append(Observation(str(game), now - timedelta(days=31 - game), player,
                                       player == "alpha" and game % 5 == 0, odds))
    model = FirstBasketModel().fit(history, now)
    for quote in model.quote([Offer("alpha", 11), Offer("beta", 15), Offer("gamma", 20)], now):
        print(quote)


if __name__ == "__main__":
    main()
