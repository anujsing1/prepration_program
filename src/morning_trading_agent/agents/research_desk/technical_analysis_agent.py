"""Technical Analysis Agent — bhavcopy OHLCV with RSI, EMA, MACD, ADX."""

from __future__ import annotations

import structlog
import pandas as pd

from morning_trading_agent.agents.research_desk.base import ResearchDeskAgent
from morning_trading_agent.application.services.indicators import (
    ADXCalculator,
    EMACalculator,
    MACDCalculator,
    MomentumCalculator,
    RelativeVolumeCalculator,
    RSICalculator,
)
from morning_trading_agent.application.services.research_desk.research_market_data_service import (
    ResearchMarketDataService,
)
from morning_trading_agent.domain.value_objects.agent_health import AgentHealth
from morning_trading_agent.domain.value_objects.research_desk import (
    ResearchDeskSnapshot,
    TechnicalAnalysisDeskOutput,
    TechnicalSetup,
)


class TechnicalAnalysisDeskAgent(ResearchDeskAgent):
    """Scan discovered symbols using real OHLCV and multi-indicator scoring."""

    name = "technical_analysis"

    def __init__(self, market_data: ResearchMarketDataService, *, max_symbols: int = 12) -> None:
        self._market = market_data
        self._max_symbols = max_symbols
        self._rsi = RSICalculator()
        self._ema20 = EMACalculator(20)
        self._ema50 = EMACalculator(50)
        self._ema200 = EMACalculator(200)
        self._macd = MACDCalculator()
        self._adx = ADXCalculator()
        self._rel_vol = RelativeVolumeCalculator()
        self._momentum = MomentumCalculator("close", 10)
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def run(self, snapshot: ResearchDeskSnapshot) -> ResearchDeskSnapshot:
        health = AgentHealth(agent=self.name, data_sources=["nse_bhavcopy", "yfinance_fallback"])
        symbols = snapshot.discovered_symbols[: self._max_symbols]
        if not symbols:
            health.errors.append("No symbols provided for technical scan")
            return self._finalize_health(snapshot, health)

        bullish: list[TechnicalSetup] = []
        bearish: list[TechnicalSetup] = []
        processed = 0

        for symbol in symbols:
            try:
                series = await self._market.load_equity_series(symbol)
            except Exception as exc:
                health.warnings.append(f"{symbol}: {exc}")
                continue
            if len(series.bars) < 25:
                health.warnings.append(f"{symbol}: insufficient bars ({len(series.bars)})")
                continue

            df = pd.DataFrame(
                {
                    "open": [b.open for b in series.bars],
                    "high": [b.high for b in series.bars],
                    "low": [b.low for b in series.bars],
                    "close": [b.close for b in series.bars],
                    "volume": [b.volume for b in series.bars],
                }
            )
            close = float(df["close"].iloc[-1])
            rsi = self._rsi.calculate(df)
            ema20 = self._ema20.calculate(df)
            ema50 = self._ema50.calculate(df)
            ema200 = self._ema200.calculate(df)
            macd_hist = self._macd.calculate(df)
            adx = self._adx.calculate(df)
            rel_vol = self._rel_vol.calculate(df)
            momentum = self._momentum.calculate(df)
            trend_score = _trend_score(close, ema20, ema50, ema200, macd_hist, adx)
            processed += 1

            if trend_score >= 62 and momentum > 0.5 and rel_vol > 1.1:
                prob = min(0.88, 0.45 + trend_score / 200.0 + momentum / 30.0)
                bullish.append(
                    TechnicalSetup(
                        symbol=symbol,
                        direction="long",
                        pattern=_pattern_label(rsi, rel_vol, momentum, bullish=True),
                        entry=round(close, 2),
                        stop=round(close * (1.0 - 0.025 - adx / 500.0), 2),
                        target=round(close * (1.0 + 0.04 + momentum / 100.0), 2),
                        probability=round(prob, 2),
                        technical_score=round(trend_score, 1),
                    )
                )
            elif trend_score <= 38 and momentum < -0.5 and rel_vol > 1.0:
                prob = min(0.88, 0.45 + (100 - trend_score) / 200.0)
                bearish.append(
                    TechnicalSetup(
                        symbol=symbol,
                        direction="short",
                        pattern=_pattern_label(rsi, rel_vol, momentum, bullish=False),
                        entry=round(close, 2),
                        stop=round(close * (1.0 + 0.025 + adx / 500.0), 2),
                        target=round(close * (1.0 - 0.04 - abs(momentum) / 100.0), 2),
                        probability=round(prob, 2),
                        technical_score=round(100 - trend_score, 1),
                    )
                )

        if processed == 0:
            health.errors.append("Technical analysis produced no valid symbol series")
            return self._finalize_health(snapshot, health)

        health.used_real_data = True
        health.records_processed = processed
        health.confidence = processed / len(symbols)
        output = TechnicalAnalysisDeskOutput(
            bullish_setups=sorted(bullish, key=lambda s: s.technical_score, reverse=True),
            bearish_setups=sorted(bearish, key=lambda s: s.technical_score, reverse=True),
        )
        self._logger.info(
            "technical_analysis_complete",
            processed=processed,
            bullish=len(output.bullish_setups),
            bearish=len(output.bearish_setups),
        )
        snapshot = snapshot.model_copy(update={"technical_analysis": output})
        return self._finalize_health(
            snapshot,
            health,
            outputs={"processed": processed, "bullish": len(bullish), "bearish": len(bearish)},
        )


def _trend_score(
    close: float, ema20: float, ema50: float, ema200: float, macd_hist: float, adx: float
) -> float:
    score = 50.0
    if close > ema20:
        score += 10
    if close > ema50:
        score += 10
    if close > ema200:
        score += 8
    if ema20 > ema50:
        score += 7
    score += max(-10.0, min(10.0, macd_hist))
    score += min(15.0, adx / 3.0)
    return max(0.0, min(100.0, score))


def _pattern_label(rsi: float, rel_vol: float, momentum: float, *, bullish: bool) -> str:
    if bullish and rel_vol > 1.5 and momentum > 2:
        return "volume_breakout"
    if bullish and rsi > 55:
        return "trend_continuation"
    if not bullish and rsi < 45:
        return "breakdown"
    return "relative_weakness" if not bullish else "relative_strength"
