"""Historical signal replay and outcome measurement."""

from datetime import date, timedelta
from statistics import mean, pstdev

import structlog

from morning_trading_agent.domain.entities.backtest import BacktestOutcome, BacktestReport, BacktestSignal
from morning_trading_agent.domain.entities.article import TradingCandidate


class BacktestEngine:
    """Computes forward returns for stored signals using price history."""

    def __init__(self, market_provider) -> None:
        self._market = market_provider
        self._logger = structlog.get_logger(self.__class__.__name__)

    def signals_from_candidates(
        self, candidates: list[TradingCandidate], *, run_date: date
    ) -> list[BacktestSignal]:
        return [
            BacktestSignal(
                run_date=run_date,
                symbol=c.stock.symbol,
                event_id=c.event_id or "",
                headline=c.sentiment.primary_catalyst_summary or c.sentiment.reason,
                catalyst_type=c.sentiment.primary_catalyst_type,
                catalyst_confidence=c.sentiment.classification_confidence,
                event_score=c.event_score or c.catalyst_score,
                technical_score=c.technical_score,
                liquidity_score=c.liquidity_score or c.institutional_tradability_score or 0.0,
                final_score=c.final_score,
                beneficiary_weight=c.beneficiary_weight,
                selection_mode=c.selection_mode,
            )
            for c in candidates
        ]

    async def evaluate_signals(
        self, signals: list[BacktestSignal], *, horizons: tuple[int, ...] = (1, 3, 5, 10)
    ) -> list[BacktestOutcome]:
        outcomes: list[BacktestOutcome] = []
        for signal in signals:
            returns = await self._forward_returns(signal.symbol, signal.run_date, horizons)
            if not returns:
                continue
            values = [r for r in returns.values() if r is not None]
            outcomes.append(
                BacktestOutcome(
                    signal=signal,
                    return_1d=returns.get(1),
                    return_3d=returns.get(3),
                    return_5d=returns.get(5),
                    return_10d=returns.get(10),
                    max_gain=max(values) if values else None,
                    max_drawdown=min(values) if values else None,
                )
            )
        return outcomes

    def aggregate(self, outcomes: list[BacktestOutcome]) -> BacktestReport:
        if not outcomes:
            today = date.today()
            return BacktestReport(start_date=today, end_date=today)

        returns_5d = [o.return_5d for o in outcomes if o.return_5d is not None]
        wins = [r for r in returns_5d if r > 0]
        avg = mean(returns_5d) if returns_5d else 0.0
        std = pstdev(returns_5d) if len(returns_5d) > 1 else 1.0
        sharpe = (avg / std) * (252**0.5) if std else 0.0
        downside = [r for r in returns_5d if r < 0]
        down_std = pstdev(downside) if len(downside) > 1 else 1.0
        sortino = (avg / down_std) * (252**0.5) if down_std else 0.0

        by_catalyst: dict[str, list[float]] = {}
        for outcome in outcomes:
            if outcome.return_5d is None:
                continue
            key = outcome.signal.catalyst_type.value
            by_catalyst.setdefault(key, []).append(outcome.return_5d)

        hit_catalyst = {k: mean(v) for k, v in by_catalyst.items() if v}
        buckets: dict[str, list[float]] = {}
        for outcome in outcomes:
            if outcome.return_5d is None:
                continue
            score = outcome.signal.final_score
            bucket = "0-60" if score < 60 else "60-75" if score < 75 else "75-85" if score < 85 else "85-100"
            buckets.setdefault(bucket, []).append(outcome.return_5d)

        return BacktestReport(
            start_date=min(o.signal.run_date for o in outcomes),
            end_date=max(o.signal.run_date for o in outcomes),
            signal_count=len(outcomes),
            win_rate=(len(wins) / len(returns_5d) * 100.0) if returns_5d else 0.0,
            average_return=avg,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            hit_rate_by_catalyst=hit_catalyst,
            hit_rate_by_score_bucket={k: mean(v) for k, v in buckets.items()},
        )

    async def _forward_returns(
        self, symbol: str, run_date: date, horizons: tuple[int, ...]
    ) -> dict[int, float | None]:
        try:
            series = await self._market.get_price_data(symbol, lookback_days=30)
        except Exception:
            return {}
        if not series.bars:
            return {}

        bars = sorted(series.bars, key=lambda b: b.timestamp)
        entry_idx = next(
            (i for i, b in enumerate(bars) if b.timestamp.date() >= run_date),
            None,
        )
        if entry_idx is None:
            return {}
        entry_close = bars[entry_idx].close
        if entry_close <= 0:
            return {}

        result: dict[int, float | None] = {}
        for horizon in horizons:
            target_idx = entry_idx + horizon
            if target_idx >= len(bars):
                result[horizon] = None
            else:
                exit_close = bars[target_idx].close
                result[horizon] = ((exit_close - entry_close) / entry_close) * 100.0
        return result
