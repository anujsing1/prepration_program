"""Escalates thematic government/defence catalysts from generic sector types."""

from morning_trading_agent.config.premarket_config import CatalystEscalationConfig
from morning_trading_agent.domain.entities.article import Article, SentimentAnalysis
from morning_trading_agent.domain.value_objects.catalyst import CatalystType


class CatalystEscalationService:
    """Deterministic escalation before magnitude/materiality scoring."""

    def __init__(self, *, config: CatalystEscalationConfig | None = None) -> None:
        self._config = config or CatalystEscalationConfig()

    def apply(
        self,
        sentiment: SentimentAnalysis,
        articles: list[Article],
    ) -> SentimentAnalysis:
        """Return sentiment with escalated catalyst type when rules match."""
        text = self._combined_text(sentiment, articles)
        current = sentiment.primary_catalyst_type
        if current not in self._config.escalatable_types:
            return sentiment

        value_crore = sentiment.llm_estimated_value_crore
        if value_crore is None:
            value_crore = self._parse_value_from_text(text)

        new_type = self._escalate_type(text, value_crore)
        if new_type is None:
            return sentiment

        return sentiment.model_copy(
            update={
                "primary_catalyst_type": new_type,
                "thematic_sector_catalyst": True,
            }
        )

    def _escalate_type(self, text: str, value_crore: float | None) -> CatalystType | None:
        lower = text.lower()
        has_defence = any(kw in lower for kw in self._config.defence_keywords)
        has_gov = any(kw in lower for kw in self._config.government_keywords)
        has_sector = any(kw in lower for kw in self._config.sector_keywords)
        large_program = (
            value_crore is not None
            and value_crore >= self._config.government_procurement_crore_threshold
        )

        if has_defence and (large_program or has_gov):
            return CatalystType.DEFENCE_PROCUREMENT
        if has_gov and large_program:
            return CatalystType.GOVERNMENT_SPENDING
        if has_gov and has_sector:
            return CatalystType.STRATEGIC_PROCUREMENT
        if has_defence or (has_sector and has_gov):
            return CatalystType.THEMATIC_DEMAND_SURGE
        if has_gov:
            return CatalystType.INDUSTRY_POLICY_CHANGE
        return None

    @staticmethod
    def _combined_text(sentiment: SentimentAnalysis, articles: list[Article]) -> str:
        parts = [sentiment.primary_catalyst_summary, sentiment.reason]
        article_map = {a.id: a for a in articles}
        for article_id in sentiment.article_ids:
            article = article_map.get(article_id)
            if article:
                parts.append(f"{article.title} {article.content}")
        return " ".join(p for p in parts if p).lower()

    @staticmethod
    def _parse_value_from_text(text: str) -> float | None:
        import re

        patterns = [
            r"₹?\s*([\d,]+(?:\.\d+)?)\s*(?:lakh|lac)\s*(?:crore|cr)?",
            r"₹?\s*([\d,]+(?:\.\d+)?)\s*(?:crore|cr)\b",
            r"([\d,]+(?:\.\d+)?)\s*(?:crore|cr)\b",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                raw = match.group(1).replace(",", "")
                try:
                    value = float(raw)
                    if "lakh" in text[match.start() : match.end() + 10].lower():
                        value /= 100.0
                    return value
                except ValueError:
                    continue
        return None
