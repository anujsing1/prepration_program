"""Portfolio Construction Agent — ranked opportunities from institutional scores."""

from __future__ import annotations

import structlog

from morning_trading_agent.agents.research_desk.base import ResearchDeskAgent
from morning_trading_agent.domain.value_objects.agent_health import AgentHealth
from morning_trading_agent.domain.value_objects.research_desk import (
    PortfolioConstructionOutput,
    ResearchDeskSnapshot,
    SymbolInstitutionalScore,
    WatchlistCandidate,
)

_MIN_CANDIDATES = 3
_MAX_CANDIDATES = 15


class PortfolioConstructionAgent(ResearchDeskAgent):
    """Build long/short/swing/high-conviction lists from ScoringAgent output."""

    name = "portfolio_construction"
    strict = True

    def __init__(self, *, max_long: int = 15, max_short: int = 15) -> None:
        self._max_long = min(max_long, _MAX_CANDIDATES)
        self._max_short = min(max_short, _MAX_CANDIDATES)
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def run(self, snapshot: ResearchDeskSnapshot) -> ResearchDeskSnapshot:
        health = AgentHealth(agent=self.name, data_sources=["scoring_agent", "technical_analysis"])
        scores: list[SymbolInstitutionalScore] = snapshot.institutional_scores
        if not scores:
            health.errors.append("No institutional scores from ScoringAgent")
            return self._finalize_health(snapshot, health)

        event_map = {e.symbol: e for e in snapshot.corporate_events.events}
        sector_map = {s.sector: s for s in snapshot.sector_rotation.sectors}
        setup_map = {
            s.symbol: s
            for s in snapshot.technical_analysis.bullish_setups + snapshot.technical_analysis.bearish_setups
        }
        news_sectors: dict[str, str] = {}
        for item in snapshot.news_intelligence.articles:
            for sym in item.stocks_affected:
                if item.sectors_affected:
                    news_sectors[sym] = item.sectors_affected[0]

        long_candidates = _build_candidates(
            scores,
            direction="long",
            setup_map=setup_map,
            event_map=event_map,
            sector_map=sector_map,
            news_sectors=news_sectors,
            min_score=45.0,
        )
        short_candidates = _build_candidates(
            sorted(scores, key=lambda s: s.final_score),
            direction="short",
            setup_map=setup_map,
            event_map=event_map,
            sector_map=sector_map,
            news_sectors=news_sectors,
            min_score=0.0,
            invert=True,
        )

        long_candidates.sort(key=lambda c: c.score, reverse=True)
        short_candidates.sort(key=lambda c: c.score, reverse=True)

        if len(long_candidates) < _MIN_CANDIDATES and len(scores) >= _MIN_CANDIDATES:
            long_candidates = _build_candidates(
                scores,
                direction="long",
                setup_map=setup_map,
                event_map=event_map,
                sector_map=sector_map,
                news_sectors=news_sectors,
                min_score=0.0,
            )[:_MAX_CANDIDATES]

        high_conviction = [c for c in long_candidates if c.confidence >= 0.65 and c.score >= 60.0][:5]
        output = PortfolioConstructionOutput(
            long_watchlist=long_candidates[: self._max_long],
            short_watchlist=short_candidates[: self._max_short],
            swing_watchlist=long_candidates[: min(8, self._max_long)],
            intraday_watchlist=[c for c in long_candidates if c.catalyst_score >= 65][:5],
            high_conviction_watchlist=high_conviction,
        )

        total = len(output.long_watchlist) + len(output.short_watchlist)
        health.used_real_data = total > 0
        health.records_processed = total
        if not health.used_real_data:
            health.errors.append("No portfolio candidates constructed")
        health.confidence = min(1.0, total / _MIN_CANDIDATES) if total else 0.0
        self._logger.info(
            "portfolio_construction_complete",
            long=len(output.long_watchlist),
            short=len(output.short_watchlist),
            high_conviction=len(output.high_conviction_watchlist),
        )
        snapshot = snapshot.model_copy(update={"portfolio": output})
        return self._finalize_health(
            snapshot,
            health,
            outputs={
                "long": len(output.long_watchlist),
                "short": len(output.short_watchlist),
                "high_conviction": len(output.high_conviction_watchlist),
            },
        )


def _build_candidates(
    scores: list[SymbolInstitutionalScore],
    *,
    direction: str,
    setup_map,
    event_map,
    sector_map,
    news_sectors: dict[str, str],
    min_score: float,
    invert: bool = False,
) -> list[WatchlistCandidate]:
    candidates: list[WatchlistCandidate] = []
    for item in scores:
        if not invert and item.final_score < min_score:
            continue
        if invert and item.final_score > 55.0:
            continue
        setup = setup_map.get(item.symbol)
        event = event_map.get(item.symbol)
        entry = setup.entry if setup and setup.entry else 0.0
        stop = setup.stop if setup and setup.stop else 0.0
        target = setup.target if setup and setup.target else 0.0
        rr = _risk_reward(entry, stop, target) if entry and stop and target else 0.0
        sector = _resolve_sector(item.symbol, sector_map, event, news_sectors)
        score_val = 100.0 - item.final_score if invert else item.final_score
        candidates.append(
            WatchlistCandidate(
                symbol=item.symbol,
                sector=sector,
                direction=direction,
                horizon="swing" if item.component_scores.get("technical_score", 0) >= 50 else "positional",
                score=round(score_val, 2),
                entry=round(entry, 2) if entry else 0.0,
                stoploss=round(stop, 2) if stop else 0.0,
                target=round(target, 2) if target else 0.0,
                risk_reward=round(rr, 2),
                confidence=item.confidence,
                composite_score=round(score_val, 2),
                sentiment_score=item.component_scores.get("news_score", 0.0),
                catalyst_score=item.component_scores.get("corporate_score", 0.0),
                institutional_score=item.component_scores.get("institutional_score", 0.0),
                technical_score=item.component_scores.get("technical_score", 0.0),
                historical_score=item.component_scores.get("historical_score", 0.0),
                sector_score=item.component_scores.get("sector_score", 0.0),
                thesis=event.title if event else (setup.pattern if setup else ""),
            )
        )
    return candidates


def _risk_reward(entry: float, stop: float, target: float) -> float:
    risk = abs(entry - stop)
    reward = abs(target - entry)
    return reward / risk if risk > 0 else 0.0


def _resolve_sector(symbol: str, sector_map: dict, event, news_sectors: dict[str, str]) -> str:
    if symbol in news_sectors:
        return news_sectors[symbol]
    if event and event.event_subtype:
        for sector in sector_map:
            if sector.lower() in event.event_subtype.lower():
                return sector
    return "General"
