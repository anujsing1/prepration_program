"""Corporate Event Agent — classified catalysts with canonical symbols."""

from __future__ import annotations

import re

import structlog

from morning_trading_agent.agents.research_desk.base import ResearchDeskAgent
from morning_trading_agent.application.services.market.canonical_symbol_service import CanonicalSymbolService
from morning_trading_agent.domain.entities.article import Article
from morning_trading_agent.domain.value_objects.agent_health import AgentHealth
from morning_trading_agent.domain.value_objects.research_desk import (
    CorporateEventAnalysis,
    CorporateEventItem,
    ResearchDeskSnapshot,
)

_CORPORATE_TYPES = {
    "EARNINGS",
    "ACQUISITION",
    "MERGER",
    "DIVIDEND",
    "BUYBACK",
    "MANAGEMENT_CHANGE",
    "REGULATORY_APPROVAL",
    "FUND_RAISING",
    "BLOCK_DEAL",
    "BOARD_MEETING",
    "INVESTOR_MEETING",
    "CORPORATE_COMMUNICATION",
}

_SUBTYPE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("Production Update", re.compile(r"production|output|capacity util", re.I)),
    ("Capacity Expansion", re.compile(r"expansion|greenfield|brownfield|new plant", re.I)),
    ("Management Guidance", re.compile(r"guidance|outlook|forecast|expects", re.I)),
    ("Acquisition", re.compile(r"acqui|merger|takeover|stake purchase", re.I)),
    ("Buyback", re.compile(r"buyback|share repurchase", re.I)),
    ("Order Win", re.compile(r"order win|contract award|bagged order", re.I)),
    ("Promoter Activity", re.compile(r"promoter|pledge|insider", re.I)),
    ("Fund Raise", re.compile(r"fund raise|qip|rights issue|placement", re.I)),
    ("Regulatory Approval", re.compile(r"approval|clearance|license|sebi|rbi", re.I)),
    ("Board Action", re.compile(r"board meeting|board approv|dividend", re.I)),
]

_DURATION_MAP = {
    "Order Win": "medium",
    "Acquisition": "long",
    "Buyback": "medium",
    "Regulatory Approval": "long",
    "Production Update": "short",
    "Management Guidance": "medium",
}


class CorporateEventAgent(ResearchDeskAgent):
    """Extract corporate catalyst events with validated NSE symbols."""

    name = "corporate_event"

    def __init__(self, symbol_service: CanonicalSymbolService) -> None:
        self._symbols = symbol_service
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def run(self, snapshot: ResearchDeskSnapshot) -> ResearchDeskSnapshot:
        health = AgentHealth(agent=self.name, data_sources=["news_articles", "nse_security_master"])
        raw_articles: list[Article] = snapshot.metadata.get("raw_articles", [])
        if not raw_articles:
            health.errors.append("No raw articles available from NewsIntelligenceAgent")
            return self._finalize_health(snapshot, health)

        await self._symbols.ensure_loaded()
        events: list[CorporateEventItem] = []
        for article in raw_articles:
            catalyst = article.catalyst_type.value
            if catalyst not in _CORPORATE_TYPES and article.source != "nse_announcements":
                continue
            text = f"{article.title} {article.content[:500]}"
            symbols = self._symbols.find_symbols_in_text(text, max_symbols=2)
            if not symbols:
                continue
            symbol = symbols[0]
            subtype = _classify_subtype(text, catalyst)
            score = float(article.catalyst_score)
            confidence = min(1.0, max(0.4, self._symbols.extraction_confidence(symbol, text)))
            impact = min(100.0, score * confidence)
            duration = _DURATION_MAP.get(subtype, "short")
            move_prob = min(1.0, (impact / 100.0))
            events.append(
                CorporateEventItem(
                    symbol=symbol,
                    event_type=catalyst,
                    event_subtype=subtype,
                    title=article.title,
                    catalyst_score=score,
                    impact_score=round(impact, 1),
                    duration=duration,
                    confidence_score=round(confidence, 2),
                    expected_move_probability=round(move_prob, 2),
                )
            )

        if not events:
            health.errors.append("No corporate events with validated NSE symbols")
            return self._finalize_health(snapshot, health)

        events.sort(key=lambda e: e.impact_score, reverse=True)
        analysis = CorporateEventAnalysis(events=events[:20])
        health.used_real_data = True
        health.records_processed = len(analysis.events)
        health.confidence = min(1.0, len(events) / max(len(raw_articles), 1))
        self._logger.info("corporate_event_complete", events=len(analysis.events))
        snapshot = snapshot.model_copy(update={"corporate_events": analysis})
        return self._finalize_health(snapshot, health, outputs={"events": len(analysis.events)})


def _classify_subtype(text: str, catalyst: str) -> str:
    for label, pattern in _SUBTYPE_PATTERNS:
        if pattern.search(text):
            return label
    fallback = {
        "EARNINGS": "Management Guidance",
        "ACQUISITION": "Acquisition",
        "MERGER": "Acquisition",
        "BUYBACK": "Buyback",
        "REGULATORY_APPROVAL": "Regulatory Approval",
        "FUND_RAISING": "Fund Raise",
        "BOARD_MEETING": "Board Action",
        "MANAGEMENT_CHANGE": "Promoter Activity",
    }
    return fallback.get(catalyst, "Production Update")
