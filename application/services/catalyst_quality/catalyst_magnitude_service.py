"""Determines catalyst magnitude from LLM, regex, and type baselines."""

from morning_trading_agent.application.services.catalyst_quality.financial_amount_parser import (
    FinancialAmountParser,
)
from morning_trading_agent.config.premarket_config import CatalystMagnitudeConfig
from morning_trading_agent.domain.entities.article import Article, SentimentAnalysis
from morning_trading_agent.domain.value_objects.catalyst import CatalystType
from morning_trading_agent.domain.value_objects.catalyst_quality import CatalystMagnitude


class CatalystMagnitudeService:
    """Hybrid magnitude: LLM fields + article regex + type baseline."""

    def __init__(
        self,
        *,
        config: CatalystMagnitudeConfig | None = None,
        parser: FinancialAmountParser | None = None,
    ) -> None:
        self._config = config or CatalystMagnitudeConfig()
        self._parser = parser or FinancialAmountParser()

    def evaluate(
        self,
        sentiment: SentimentAnalysis,
        articles: list[Article],
        *,
        llm_magnitude: CatalystMagnitude | None = None,
        llm_value_crore: float | None = None,
    ) -> tuple[CatalystMagnitude, float, float | None, str]:
        """Return magnitude, magnitude_score, financial_value_crore, source."""
        linked_text = self._linked_article_text(sentiment, articles)
        regex_value = self._parser.parse_max_value_crore(linked_text)
        if regex_value is not None:
            regex_value = min(regex_value, self._config.max_value_crore_sanity)

        value_crore = self._merge_values(llm_value_crore, regex_value)
        type_baseline = self._config.type_baseline_magnitude.get(
            sentiment.primary_catalyst_type, CatalystMagnitude.MEDIUM
        )

        if value_crore is not None:
            value_magnitude = self._config.magnitude_for_value_crore(value_crore)
            magnitude = self._max_magnitude(value_magnitude, type_baseline, llm_magnitude)
            source = "regex" if regex_value and regex_value >= (llm_value_crore or 0) else "llm"
            if regex_value and llm_value_crore:
                source = "hybrid"
        elif llm_magnitude is not None:
            magnitude = self._max_magnitude(llm_magnitude, type_baseline)
            source = "llm"
        else:
            magnitude = type_baseline
            source = "baseline"

        score = self._config.score_for_magnitude(magnitude)
        return magnitude, score, value_crore, source

    @staticmethod
    def _linked_article_text(sentiment: SentimentAnalysis, articles: list[Article]) -> str:
        article_map = {article.id: article for article in articles}
        parts: list[str] = []
        for article_id in sentiment.article_ids:
            article = article_map.get(article_id)
            if article:
                parts.append(f"{article.title} {article.content}")
        if not parts and sentiment.primary_catalyst_summary:
            parts.append(sentiment.primary_catalyst_summary)
        parts.append(sentiment.reason)
        return " ".join(parts)

    @staticmethod
    def _merge_values(
        llm_value: float | None, regex_value: float | None
    ) -> float | None:
        if llm_value is None and regex_value is None:
            return None
        if llm_value is None:
            return regex_value
        if regex_value is None:
            return llm_value
        return max(llm_value, regex_value)

    @staticmethod
    def _max_magnitude(
        *levels: CatalystMagnitude | None,
    ) -> CatalystMagnitude:
        order = [
            CatalystMagnitude.VERY_LOW,
            CatalystMagnitude.LOW,
            CatalystMagnitude.MEDIUM,
            CatalystMagnitude.HIGH,
            CatalystMagnitude.VERY_HIGH,
        ]
        present = [level for level in levels if level is not None]
        if not present:
            return CatalystMagnitude.MEDIUM
        return max(present, key=lambda m: order.index(m))
