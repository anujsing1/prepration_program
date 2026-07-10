"""Market Structure Agent — NSE indices + bhavcopy breadth."""

from __future__ import annotations

from dataclasses import asdict

import structlog

from morning_trading_agent.agents.research_desk.base import ResearchDeskAgent
from morning_trading_agent.application.services.research_desk.research_market_data_service import (
    INDEX_ALIASES,
    ResearchMarketDataService,
)
from morning_trading_agent.domain.value_objects.agent_health import AgentHealth
from morning_trading_agent.domain.value_objects.research_desk import MarketStructureAnalysis, ResearchDeskSnapshot


class MarketStructureAgent(ResearchDeskAgent):
    """Analyze NIFTY, BANKNIFTY, MIDCAP, SMALLCAP, INDIA VIX with real NSE + breadth data."""

    name = "market_structure"

    def __init__(self, market_data: ResearchMarketDataService) -> None:
        self._market = market_data
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def run(self, snapshot: ResearchDeskSnapshot) -> ResearchDeskSnapshot:
        health = AgentHealth(agent=self.name, data_sources=["nse_allIndices", "nse_bhavcopy"])
        indices, breadth = await self._market.load_india_snapshot()

        if not indices and breadth is None:
            health.errors.append("NSE indices and bhavcopy breadth unavailable")
            return self._finalize_health(snapshot, health)

        health.used_real_data = True
        health.records_processed = len(indices) + (1 if breadth else 0)

        index_payload: dict[str, dict[str, float | str | int]] = {}
        bullish = bearish = 0
        momentum_sum = 0.0
        count = 0
        vix_change = 0.0

        for label in INDEX_ALIASES:
            snap = self._market.index_for_label(indices, label)
            if snap is None:
                continue
            count += 1
            trend = "bullish" if snap.change_pct > 0.2 else "bearish" if snap.change_pct < -0.2 else "neutral"
            if trend == "bullish":
                bullish += 1
            elif trend == "bearish":
                bearish += 1
            momentum_sum += snap.change_pct
            if label == "INDIA_VIX":
                vix_change = snap.change_pct
            index_payload[label] = {
                "close": snap.last,
                "momentum_pct": snap.change_pct,
                "trend": trend,
                "advances": snap.advance,
                "declines": snap.decline,
                "volume": snap.volume,
            }

        if count == 0:
            health.errors.append("No benchmark indices resolved from NSE")
            health.used_real_data = False
            return self._finalize_health(snapshot, health)

        avg_momentum = momentum_sum / count
        breadth_score = breadth.breadth_score if breadth else (bullish / count * 100.0)
        ad_ratio = breadth.advance_decline_ratio if breadth else bullish / max(bearish, 1)

        if avg_momentum > 0.4 and breadth_score >= 55:
            regime, trend = "risk_on_uptrend", "bullish"
        elif avg_momentum < -0.4 and breadth_score <= 45:
            regime, trend = "risk_off_downtrend", "bearish"
        else:
            regime, trend = "range_bound", "neutral"

        vix_level = float(index_payload.get("INDIA_VIX", {}).get("close", 15.0))
        vol_regime = "elevated" if vix_level > 18 or vix_change > 3 else "compressed" if vix_level < 13 else "normal"
        risk_score = min(100.0, max(0.0, 30.0 + vix_level * 2.5 - avg_momentum * 3.0 - breadth_score * 0.2))
        continuation = min(1.0, max(0.0, 0.35 + breadth_score / 200.0 + avg_momentum / 25.0))

        analysis = MarketStructureAnalysis(
            market_regime=regime,
            trend=trend,
            breadth_score=round(breadth_score, 1),
            risk_score=round(risk_score, 1),
            continuation_probability=round(continuation, 2),
            indices=index_payload,
            volatility_regime=vol_regime,
        )
        snapshot.metadata["market_breadth"] = asdict(breadth) if breadth else {}
        snapshot.metadata["advance_decline_ratio"] = ad_ratio
        health.confidence = min(1.0, count / len(INDEX_ALIASES))
        self._logger.info("market_structure_complete", regime=regime, breadth=breadth_score, indices=count)
        snapshot = snapshot.model_copy(update={"market_structure": analysis})
        return self._finalize_health(
            snapshot,
            health,
            outputs={"regime": regime, "breadth_score": breadth_score, "indices_loaded": count},
        )
