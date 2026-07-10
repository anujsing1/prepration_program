"""News Intelligence Agent — enriched news with canonical symbol extraction."""

from __future__ import annotations

import structlog

from morning_trading_agent.agents.research_desk.base import ResearchDeskAgent
from morning_trading_agent.application.services.market.canonical_symbol_service import CanonicalSymbolService
from morning_trading_agent.application.services.news.news_aggregator_service import NewsAggregatorService
from morning_trading_agent.domain.value_objects.agent_health import AgentHealth
from morning_trading_agent.domain.value_objects.research_desk import (
    NewsIntelligenceAnalysis,
    NewsIntelligenceItem,
    ResearchDeskSnapshot,
)


class NewsIntelligenceAgent(ResearchDeskAgent):
    """Collect and enrich news using real providers and NSE symbol resolution."""

    name = "news_intelligence"

    def __init__(
        self,
        news_aggregator: NewsAggregatorService,
        symbol_service: CanonicalSymbolService,
        *,
        fetch_limit: int = 50,
    ) -> None:
        self._news = news_aggregator
        self._symbols = symbol_service
        self._fetch_limit = fetch_limit
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def run(self, snapshot: ResearchDeskSnapshot) -> ResearchDeskSnapshot:
        health = AgentHealth(
            agent=self.name,
            data_sources=["news_providers", "nse_security_master"],
        )
        articles, stats = await self._news.collect(limit=self._fetch_limit)
        if not articles:
            health.errors.append("No articles collected from configured news providers")
            return self._finalize_health(snapshot, health)

        await self._symbols.ensure_loaded()
        items: list[NewsIntelligenceItem] = []
        high_impact = 0
        bullish = bearish = 0

        for article in articles:
            text = f"{article.title} {article.content[:800]}"
            symbols = self._symbols.find_symbols_in_text(text, max_symbols=4)
            catalyst = article.catalyst_type.value
            impact = float(article.catalyst_score)
            if impact >= 70:
                high_impact += 1
            sentiment_label = _sentiment_from_priority(article.priority_score, article.catalyst_score)
            if sentiment_label == "bullish":
                bullish += 1
            elif sentiment_label == "bearish":
                bearish += 1
            items.append(
                NewsIntelligenceItem(
                    article_id=str(article.id),
                    title=article.title,
                    source=article.source,
                    sentiment=sentiment_label,
                    impact_score=impact,
                    duration=_duration_from_catalyst(catalyst),
                    sectors_affected=_sectors_from_text(article.title),
                    stocks_affected=symbols,
                )
            )

        if bullish > bearish * 1.3:
            macro = "bullish"
        elif bearish > bullish * 1.3:
            macro = "bearish"
        else:
            macro = "neutral"

        analysis = NewsIntelligenceAnalysis(
            articles=items,
            macro_sentiment=macro,
            high_impact_count=high_impact,
        )
        snapshot.metadata["raw_articles"] = articles
        snapshot.metadata["news_stats"] = stats.model_dump() if hasattr(stats, "model_dump") else {}

        health.used_real_data = True
        health.records_processed = len(items)
        health.confidence = min(1.0, len(items) / max(self._fetch_limit, 1))
        self._logger.info("news_intelligence_complete", articles=len(items), high_impact=high_impact)
        snapshot = snapshot.model_copy(update={"news_intelligence": analysis})
        return self._finalize_health(
            snapshot,
            health,
            outputs={"articles": len(items), "high_impact": high_impact, "macro": macro},
        )


def _sentiment_from_priority(priority: float, catalyst_score: float) -> str:
    blended = priority * 0.4 + catalyst_score * 0.6
    if blended >= 65:
        return "bullish"
    if blended <= 40:
        return "bearish"
    return "neutral"


def _duration_from_catalyst(catalyst: str) -> str:
    if catalyst in {"EARNINGS", "ACQUISITION", "MERGER", "REGULATORY_APPROVAL", "BUYBACK"}:
        return "medium"
    if catalyst in {"POLICY_BENEFICIARY", "SECTOR_TAILWIND"}:
        return "long"
    return "short"


def _sectors_from_text(text: str) -> list[str]:
    lowered = text.lower()
    mapping = {
        "bank": "Banking",
        "pharma": "Pharma",
        "auto": "Auto",
        "defence": "Defence",
        "defense": "Defence",
        "infra": "Infra",
        "metal": "Metals",
        "oil": "Energy",
        "fmcg": "FMCG",
        " it ": "IT",
    }
    return [sector for key, sector in mapping.items() if key in lowered]
