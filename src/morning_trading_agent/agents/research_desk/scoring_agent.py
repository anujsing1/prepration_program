"""Scoring Agent — institutional per-symbol scoring across all discovered symbols."""

from __future__ import annotations

import structlog

from morning_trading_agent.agents.research_desk.base import ResearchDeskAgent
from morning_trading_agent.domain.value_objects.agent_health import AgentHealth
from morning_trading_agent.domain.value_objects.research_desk import (
    ResearchDeskSnapshot,
    SymbolInstitutionalScore,
)

_WEIGHTS = {
    "technical_score": 0.20,
    "news_score": 0.15,
    "corporate_score": 0.10,
    "institutional_score": 0.15,
    "sector_score": 0.10,
    "global_score": 0.10,
    "options_score": 0.10,
    "historical_score": 0.05,
    "risk_score": 0.05,
}


class ScoringAgent(ResearchDeskAgent):
    """Compute unified per-symbol score components from upstream agents."""

    name = "scoring"
    strict = True

    def __init__(self) -> None:
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def run(self, snapshot: ResearchDeskSnapshot) -> ResearchDeskSnapshot:
        health = AgentHealth(agent=self.name, data_sources=["upstream_agents"])
        symbols = list(dict.fromkeys(snapshot.discovered_symbols))
        if not symbols:
            health.errors.append("No discovered symbols to score")
            return self._finalize_health(snapshot, health)

        sector_map = {s.sector: s for s in snapshot.sector_rotation.sectors}
        event_map = {e.symbol: e for e in snapshot.corporate_events.events}
        news_map: dict[str, float] = {}
        for item in snapshot.news_intelligence.articles:
            for sym in item.stocks_affected:
                news_map[sym] = max(news_map.get(sym, 0.0), item.impact_score)

        tech_map: dict[str, float] = {}
        for setup in snapshot.technical_analysis.bullish_setups + snapshot.technical_analysis.bearish_setups:
            tech_map[setup.symbol] = setup.technical_score

        inst_base = snapshot.institutional_flow.institutional_confidence_score
        hist_base = snapshot.historical_context.historical_probability_score * 100.0
        global_base = 100.0 - snapshot.global_market.global_risk_score
        options_base = _options_score(snapshot)
        risk_base = 100.0 - snapshot.market_structure.risk_score

        scores: list[SymbolInstitutionalScore] = []
        for sym in symbols:
            event = event_map.get(sym)
            sector_item = _sector_for_symbol(sym, sector_map, event)
            sector_score = _sector_score(sector_item)
            corporate_score = (event.impact_score or event.catalyst_score) if event else 0.0

            components = {
                "technical_score": tech_map.get(sym, _fallback_technical(sym, tech_map)),
                "news_score": news_map.get(sym, 0.0),
                "corporate_score": corporate_score,
                "institutional_score": inst_base,
                "sector_score": sector_score,
                "global_score": global_base,
                "options_score": options_base,
                "historical_score": hist_base,
                "risk_score": risk_base,
            }
            final = sum(components[k] * _WEIGHTS[k] for k in _WEIGHTS)
            confidence = _score_confidence(components, sym in tech_map, event is not None)
            scores.append(
                SymbolInstitutionalScore(
                    symbol=sym,
                    component_scores={k: round(v, 2) for k, v in components.items()},
                    final_score=round(final, 2),
                    confidence=round(confidence, 2),
                )
            )

        scores.sort(key=lambda s: s.final_score, reverse=True)
        snapshot.metadata["symbol_scores"] = {s.symbol: s.component_scores for s in scores}
        health.used_real_data = True
        health.records_processed = len(scores)
        health.confidence = min(1.0, len(scores) / max(len(symbols), 1))
        self._logger.info("scoring_complete", symbols=len(scores))
        snapshot = snapshot.model_copy(update={"institutional_scores": scores})
        return self._finalize_health(snapshot, health, outputs={"scored_symbols": len(scores)})


def _options_score(snapshot: ResearchDeskSnapshot) -> float:
    opts = snapshot.options_flow
    if opts.pcr <= 0:
        return 0.0
    pcr_component = min(100.0, opts.pcr * 55.0)
    conf_component = opts.confidence * 30.0
    return min(100.0, pcr_component + conf_component)


def _sector_for_symbol(sym, sector_map, event):
    if event and event.event_subtype:
        for sector in sector_map:
            if sector.lower() in event.event_subtype.lower():
                return sector_map[sector]
    return next(iter(sector_map.values()), None) if sector_map else None


def _sector_score(sector_item) -> float:
    if sector_item is None:
        return 0.0
    return min(100.0, max(0.0, sector_item.relative_strength * 15.0 + sector_item.momentum_pct * 8.0))


def _fallback_technical(sym: str, tech_map: dict[str, float]) -> float:
    if not tech_map:
        return 0.0
    avg = sum(tech_map.values()) / len(tech_map)
    return max(0.0, avg * 0.35)


def _score_confidence(components: dict[str, float], has_technical: bool, has_event: bool) -> float:
    signals = sum(1 for v in components.values() if v > 0)
    base = signals / len(components)
    if has_technical:
        base += 0.15
    if has_event:
        base += 0.1
    return min(1.0, base)
