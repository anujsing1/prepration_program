"""Global Market Agent — overnight global risk from yfinance + Stooq."""

from __future__ import annotations

import structlog

from morning_trading_agent.agents.research_desk.base import ResearchDeskAgent
from morning_trading_agent.application.services.research_desk.global_market_fetcher import GlobalMarketDataError
from morning_trading_agent.application.services.research_desk.research_market_data_service import (
    ResearchMarketDataService,
)
from morning_trading_agent.domain.value_objects.agent_health import AgentHealth
from morning_trading_agent.domain.value_objects.research_desk import GlobalMarketAnalysis, ResearchDeskSnapshot

_EQUITY_LABELS = {
    "SP500",
    "NASDAQ",
    "DOW",
    "RUSSELL2000",
    "NIKKEI",
    "HANGSENG",
    "DAX",
    "FTSE",
}
_COMMODITY_LABELS = {"BRENT", "WTI", "GOLD", "SILVER"}
_YIELD_LABELS = {"US10Y", "DXY"}


class GlobalMarketAgent(ResearchDeskAgent):
    """Analyze US, Europe, Asia, commodities, and yields."""

    name = "global_market"
    strict = True

    def __init__(self, market_data: ResearchMarketDataService) -> None:
        self._market = market_data
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def run(self, snapshot: ResearchDeskSnapshot) -> ResearchDeskSnapshot:
        health = AgentHealth(agent=self.name, data_sources=["tradingview", "yfinance", "stooq"])
        try:
            metrics = await self._market.load_global_indices()
        except GlobalMarketDataError as exc:
            health.errors.append(str(exc))
            return self._finalize_health(snapshot, health)

        health.used_real_data = True
        health.records_processed = len(metrics)
        markets: dict[str, dict[str, float | str]] = {}
        commodities: dict[str, float] = {}
        equity_momentums: list[float] = []
        bullish_global = 0
        risk_signals = 0.0

        for item in metrics:
            payload = {
                "close": item.last_close,
                "momentum_pct": item.momentum_pct,
                "trend": item.trend,
                "source": item.source,
            }
            if item.label in _COMMODITY_LABELS or item.label in _YIELD_LABELS:
                commodities[item.label] = item.last_close
            else:
                markets[item.label] = payload
            if item.label in _EQUITY_LABELS:
                equity_momentums.append(item.momentum_pct)
                risk_signals += abs(item.momentum_pct)
                if item.momentum_pct > 0:
                    bullish_global += 1

        equity_count = max(1, len(equity_momentums))
        risk_score = min(100.0, 20.0 + risk_signals / equity_count * 5.0)
        bullish_ratio = bullish_global / equity_count

        if bullish_ratio >= 0.6:
            sentiment, india_bias, risk_on, risk_off = "risk_on", "gap_up", True, False
        elif bullish_ratio <= 0.35:
            sentiment, india_bias, risk_on, risk_off = "risk_off", "gap_down", False, True
        else:
            india_trend = snapshot.market_structure.trend
            sentiment = "risk_on" if india_trend == "bullish" else "risk_off"
            india_bias = "flat_to_positive" if india_trend == "bullish" else "flat_to_negative"
            risk_on = india_trend == "bullish"
            risk_off = india_trend == "bearish"

        correlation = _correlation_score(equity_momentums)

        analysis = GlobalMarketAnalysis(
            global_risk_score=round(risk_score, 1),
            overnight_sentiment=sentiment,
            expected_india_opening_bias=india_bias,
            risk_on=risk_on,
            risk_off=risk_off,
            correlation_score=round(correlation, 3),
            markets=markets,
            commodities=commodities,
        )
        health.confidence = min(1.0, len(metrics) / 14.0)
        self._logger.info(
            "global_market_complete",
            sentiment=sentiment,
            markets=len(metrics),
            correlation=correlation,
        )
        snapshot = snapshot.model_copy(update={"global_market": analysis})
        return self._finalize_health(
            snapshot,
            health,
            outputs={"markets": len(metrics), "sentiment": sentiment, "correlation": correlation},
        )


def _correlation_score(momentums: list[float]) -> float:
    if len(momentums) < 2:
        return 0.0
    positive = sum(1 for m in momentums if m > 0)
    negative = sum(1 for m in momentums if m < 0)
    aligned = max(positive, negative)
    return aligned / len(momentums)
