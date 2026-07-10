"""Walk-forward grid search for ranking V3 weights."""

from itertools import product

from morning_trading_agent.config.premarket_config import RankingWeightV3Config
from morning_trading_agent.domain.entities.backtest import BacktestOutcome


class WeightOptimizer:
    """Simple grid search optimizer for ranking weights."""

    def optimize(
        self,
        outcomes: list[BacktestOutcome],
        *,
        objective: str = "sortino",
    ) -> RankingWeightV3Config:
        if not outcomes:
            return RankingWeightV3Config()

        best_config = RankingWeightV3Config()
        best_score = float("-inf")
        grid = [0.35, 0.40, 0.45]
        for event_w, tech_w, liq_w in product(grid, repeat=3):
            if abs(event_w + tech_w + liq_w - 0.90) > 0.01:
                continue
            sent_w, fresh_w = 0.05, 0.05
            score = self._evaluate_weights(
                outcomes,
                event_w,
                tech_w,
                liq_w,
                sent_w,
                fresh_w,
                objective=objective,
            )
            if score > best_score:
                best_score = score
                best_config = RankingWeightV3Config(
                    event=event_w,
                    technical=tech_w,
                    liquidity=liq_w,
                    sentiment=sent_w,
                    freshness=fresh_w,
                )
        return best_config

    @staticmethod
    def _evaluate_weights(
        outcomes: list[BacktestOutcome],
        event_w: float,
        tech_w: float,
        liq_w: float,
        sent_w: float,
        fresh_w: float,
        *,
        objective: str,
    ) -> float:
        weighted_returns: list[float] = []
        for outcome in outcomes:
            if outcome.return_5d is None:
                continue
            signal = outcome.signal
            proxy_rank = (
                event_w * signal.event_score
                + tech_w * signal.technical_score
                + liq_w * signal.liquidity_score
            )
            weighted_returns.append(outcome.return_5d * (proxy_rank / 100.0))

        if not weighted_returns:
            return 0.0
        avg = sum(weighted_returns) / len(weighted_returns)
        if objective == "average":
            return avg
        negatives = [r for r in weighted_returns if r < 0]
        if not negatives:
            return avg
        down_var = sum(r * r for r in negatives) / len(negatives)
        down_std = down_var**0.5
        return avg / down_std if down_std else avg
