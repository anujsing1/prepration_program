"""Historical Context Agent — RAG over market memory."""

from __future__ import annotations

import structlog

from morning_trading_agent.agents.research_desk.base import ResearchDeskAgent
from morning_trading_agent.application.services.memory.market_memory_index import MarketMemoryIndex
from morning_trading_agent.domain.value_objects.agent_health import AgentHealth
from morning_trading_agent.domain.value_objects.research_desk import (
    HistoricalAnalogue,
    HistoricalContextAnalysis,
    ResearchDeskSnapshot,
)


class HistoricalContextAgent(ResearchDeskAgent):
    """Retrieve similar historical sessions from market memory."""

    name = "historical_context"
    strict = False

    def __init__(self, memory_index: MarketMemoryIndex, *, top_k: int = 5) -> None:
        self._index = memory_index
        self._top_k = top_k
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def run(self, snapshot: ResearchDeskSnapshot) -> ResearchDeskSnapshot:
        health = AgentHealth(agent=self.name, data_sources=["market_memory_rag"])
        queries = [
            (
                "market_summary",
                f"regime {snapshot.market_regime.regime} breadth {snapshot.market_structure.breadth_score} "
                f"trend {snapshot.market_structure.trend}",
            ),
            (
                "sector_rotation",
                f"leaders {', '.join(snapshot.sector_rotation.leaders)} "
                f"laggards {', '.join(snapshot.sector_rotation.laggards)}",
            ),
            (
                "institutional",
                f"fii {snapshot.institutional_flow.fii_net} dii {snapshot.institutional_flow.dii_net} "
                f"{snapshot.institutional_flow.smart_money_direction}",
            ),
            (
                "options",
                f"pcr {snapshot.options_flow.pcr} max_pain {snapshot.options_flow.max_pain}",
            ),
        ]
        all_hits = []
        for category, query in queries:
            hits = await self._index.search(query, category=category, top_k=self._top_k)
            all_hits.extend(hits)

        health.used_real_data = True
        health.records_processed = len(all_hits)
        seen: set[str] = set()
        analogues: list[HistoricalAnalogue] = []
        for hit in sorted(all_hits, key=lambda h: h.score, reverse=True):
            if hit.date in seen:
                continue
            seen.add(hit.date)
            analogues.append(
                HistoricalAnalogue(
                    date=hit.date,
                    similarity_score=hit.score,
                    summary=hit.text[:500],
                    outcome=_outcome_from_hit(hit.text),
                )
            )
            if len(analogues) >= self._top_k:
                break

        if analogues:
            avg_score = sum(a.similarity_score for a in analogues) / len(analogues)
            positive = sum(1 for a in analogues if "positive" in a.outcome)
            negative = sum(1 for a in analogues if "negative" in a.outcome)
            hist_prob = positive / (positive + negative) if (positive + negative) > 0 else avg_score
            confidence = min(1.0, avg_score)
            narrative = (
                f"Retrieved {len(analogues)} historical analogues (market days, sector rotations, "
                f"institutional setups). Dominant follow-through: {_dominant_outcome(analogues)}."
            )
            health.confidence = confidence
        else:
            hist_prob = 0.0
            confidence = 0.0
            narrative = "No prior market memory matches — session will seed future RAG retrieval."
            health.warnings.append("empty_rag_hits")

        analysis = HistoricalContextAnalysis(
            analogues=analogues,
            historical_probability_score=round(hist_prob, 2),
            confidence_score=round(confidence, 2),
            narrative=narrative,
        )
        self._logger.info("historical_context_complete", analogues=len(analogues))
        snapshot = snapshot.model_copy(update={"historical_context": analysis})
        return self._finalize_health(snapshot, health, outputs={"analogues": len(analogues)})


def _outcome_from_hit(text: str) -> str:
    lowered = text.lower()
    if "bullish" in lowered or "risk_on" in lowered or "gap_up" in lowered:
        return "positive_follow_through"
    if "bearish" in lowered or "risk_off" in lowered or "gap_down" in lowered:
        return "negative_follow_through"
    return "mixed"


def _dominant_outcome(analogues: list[HistoricalAnalogue]) -> str:
    outcomes = [a.outcome for a in analogues if a.outcome]
    if not outcomes:
        return "insufficient_data"
    positive = sum(1 for o in outcomes if "positive" in o)
    negative = sum(1 for o in outcomes if "negative" in o)
    if positive > negative:
        return "positive"
    if negative > positive:
        return "negative"
    return "mixed"
