"""Applies broker downgrade and strong-catalyst override to catalyst score."""

from morning_trading_agent.config.premarket_config import BrokerRatingConfig
from morning_trading_agent.config.premarket_config import CatalystScoreConfig
from morning_trading_agent.domain.entities.article import Article, SentimentAnalysis
from morning_trading_agent.domain.value_objects.catalyst import CatalystType
from morning_trading_agent.domain.value_objects.catalyst_quality import BROKER_CATALYST_TYPES


class EffectiveCatalystScoreService:
    """Caps broker-only catalysts unless a strong event is co-mentioned."""

    def __init__(
        self,
        *,
        broker_config: BrokerRatingConfig | None = None,
        score_config: CatalystScoreConfig | None = None,
    ) -> None:
        self._broker = broker_config or BrokerRatingConfig()
        self._scores = score_config or CatalystScoreConfig()

    def effective_score(
        self,
        sentiment: SentimentAnalysis,
        articles: list[Article],
        *,
        base_catalyst_score: float | None = None,
    ) -> float:
        base = base_catalyst_score if base_catalyst_score is not None else sentiment.catalyst_score
        catalyst_type = sentiment.primary_catalyst_type

        if catalyst_type not in BROKER_CATALYST_TYPES:
            return base

        if self._has_strong_override(sentiment, articles):
            strong_score = max(
                self._scores.score_for(t) for t in self._broker.strong_override_types
            )
            return max(base, min(strong_score, base * 2))

        return min(base, self._broker.broker_only_catalyst_score)

    def _has_strong_override(
        self, sentiment: SentimentAnalysis, articles: list[Article]
    ) -> bool:
        text = f"{sentiment.reason} {sentiment.primary_catalyst_summary}".lower()
        article_map = {a.id: a for a in articles}
        for article_id in sentiment.article_ids:
            article = article_map.get(article_id)
            if article:
                text += f" {article.title} {article.content}".lower()

        if any(keyword in text for keyword in self._broker.strong_override_keywords):
            return True

        for article_id in sentiment.article_ids:
            article = article_map.get(article_id)
            if article and article.catalyst_type in self._broker.strong_override_types:
                return True

        return False
