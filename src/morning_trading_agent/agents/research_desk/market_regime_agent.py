"""Market Regime Agent — institutional regime classification."""

from __future__ import annotations

import structlog

from morning_trading_agent.agents.research_desk.base import ResearchDeskAgent
from morning_trading_agent.domain.value_objects.agent_health import AgentHealth
from morning_trading_agent.domain.value_objects.research_desk import MarketRegimeAnalysis, ResearchDeskSnapshot

_REGIMES = (
    "ACCUMULATION",
    "DISTRIBUTION",
    "ROTATION",
    "BREAKOUT",
    "CONSOLIDATION",
    "TRENDING",
    "MOMENTUM",
    "RISK_ON",
    "RISK_OFF",
    "PANIC",
    "MEAN_REVERSION",
)


class MarketRegimeAgent(ResearchDeskAgent):
    """Classify market regime from breadth, VIX, flow, global, and options."""

    name = "market_regime"
    strict = False

    def __init__(self) -> None:
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def run(self, snapshot: ResearchDeskSnapshot) -> ResearchDeskSnapshot:
        health = AgentHealth(agent=self.name, data_sources=["upstream_agents"])
        ms = snapshot.market_structure
        flow = snapshot.institutional_flow
        global_m = snapshot.global_market
        opts = snapshot.options_flow
        sectors = snapshot.sector_rotation

        breadth = ms.breadth_score
        vix_data = ms.indices.get("INDIA_VIX", {})
        vix_level = float(vix_data.get("close", 15.0)) if vix_data else 15.0
        fii = flow.fii_net or 0.0
        dii = flow.dii_net or 0.0
        pcr = opts.pcr if opts.pcr > 0 else 1.0

        regime, bull_prob, bear_prob = _classify_regime(
            breadth=breadth,
            vix=vix_level,
            trend=ms.trend,
            fii=fii,
            dii=dii,
            global_sentiment=global_m.overnight_sentiment,
            pcr=pcr,
            leaders=sectors.leaders,
            laggards=sectors.laggards,
        )
        confidence = _regime_confidence(ms, flow, global_m, opts)

        analysis = MarketRegimeAnalysis(
            regime=regime,
            confidence=round(confidence, 2),
            bullish_probability=round(bull_prob, 2),
            bearish_probability=round(bear_prob, 2),
        )
        health.used_real_data = True
        health.records_processed = 1
        health.confidence = confidence
        self._logger.info("market_regime_complete", regime=regime, confidence=confidence)
        snapshot = snapshot.model_copy(update={"market_regime": analysis})
        return self._finalize_health(
            snapshot,
            health,
            outputs={"regime": regime, "bullish_probability": bull_prob},
        )


def _classify_regime(
    *,
    breadth: float,
    vix: float,
    trend: str,
    fii: float,
    dii: float,
    global_sentiment: str,
    pcr: float,
    leaders: list[str],
    laggards: list[str],
) -> tuple[str, float, float]:
    if vix > 22 and breadth < 40:
        return "PANIC", 0.15, 0.85
    if vix > 18 and fii < -500:
        return "RISK_OFF", 0.25, 0.75
    if global_sentiment == "risk_on" and breadth >= 58 and trend == "bullish":
        return "RISK_ON", 0.72, 0.28
    if global_sentiment == "risk_off" and breadth <= 42:
        return "RISK_OFF", 0.28, 0.72
    if leaders and laggards and leaders[0] != laggards[0]:
        return "ROTATION", 0.52, 0.48
    if breadth >= 60 and dii > 0 and pcr > 1.0:
        return "ACCUMULATION", 0.65, 0.35
    if breadth <= 42 and fii < 0 and pcr < 0.95:
        return "DISTRIBUTION", 0.32, 0.68
    if trend == "bullish" and breadth >= 55:
        return "TRENDING", 0.62, 0.38
    if abs(breadth - 50) < 5 and vix < 16:
        return "CONSOLIDATION", 0.48, 0.52
    if trend == "bullish" and breadth >= 52:
        return "MOMENTUM", 0.58, 0.42
    if breadth < 48 and breadth > 42:
        return "MEAN_REVERSION", 0.45, 0.55
    if trend == "bullish":
        return "BREAKOUT", 0.55, 0.45
    return "CONSOLIDATION", 0.5, 0.5


def _regime_confidence(ms, flow, global_m, opts) -> float:
    signals = 0.0
    if ms.breadth_score > 0:
        signals += 0.25
    if flow.fii_net is not None:
        signals += 0.2
    if global_m.overnight_sentiment:
        signals += 0.2
    if opts.pcr > 0:
        signals += 0.2
    if ms.indices:
        signals += 0.15
    return min(1.0, signals)
