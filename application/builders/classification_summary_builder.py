"""Builds catalyst type histograms from workflow state."""

from collections import Counter

from morning_trading_agent.domain.entities.article import Article, SentimentAnalysis
from morning_trading_agent.domain.value_objects.news_metadata import NewsIngestionStats
from morning_trading_agent.graph.state import TradingState


class ClassificationSummaryBuilder:
    """Aggregates catalyst classification counts for diagnostics."""

    def from_state(self, state: TradingState) -> dict[str, int]:
        """Count catalyst types from sentiments and ingestion stats."""
        counts: Counter[str] = Counter()

        for sentiment in state.get("sentiment_results", []):
            counts[sentiment.primary_catalyst_type.value] += 1

        stats: NewsIngestionStats | None = state.get("ingestion_stats")
        if stats:
            for catalyst_type, count in stats.catalysts_identified.items():
                counts[f"article:{catalyst_type}"] += count

        return dict(sorted(counts.items(), key=lambda x: (-x[1], x[0])))

    def from_sentiments(self, sentiments: list[SentimentAnalysis]) -> dict[str, int]:
        """Count primary catalyst types from sentiment results."""
        counts: Counter[str] = Counter()
        for sentiment in sentiments:
            counts[sentiment.primary_catalyst_type.value] += 1
        return dict(sorted(counts.items(), key=lambda x: (-x[1], x[0])))

    def from_articles(self, articles: list[Article]) -> dict[str, int]:
        """Count catalyst types from ingested articles."""
        counts: Counter[str] = Counter()
        for article in articles:
            counts[article.catalyst_type.value] += 1
        return dict(sorted(counts.items(), key=lambda x: (-x[1], x[0])))
