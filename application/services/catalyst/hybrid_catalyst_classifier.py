"""Rule-first hybrid catalyst classification with LLM fallback."""

import re

import structlog

from morning_trading_agent.application.services.catalyst.catalyst_headline_refinement_service import (
    CatalystHeadlineRefinementService,
)
from morning_trading_agent.application.services.catalyst.catalyst_scoring_service import (
    CatalystScoringService,
)
from morning_trading_agent.application.services.news.catalyst_analysis_service import (
    CatalystAnalysisService,
)
from morning_trading_agent.config.premarket_config import HybridCatalystConfig
from morning_trading_agent.domain.entities.article import Article, SentimentAnalysis
from morning_trading_agent.domain.value_objects.catalyst import CatalystType

_ALIAS_MAP: dict[CatalystType, CatalystType] = {
    CatalystType.DEFENCE_ORDER: CatalystType.DEFENCE_PROCUREMENT,
    CatalystType.MAJOR_ORDER_WIN: CatalystType.ORDER_WIN,
    CatalystType.STRATEGIC_PARTNERSHIP: CatalystType.PARTNERSHIP,
    CatalystType.FDA_APPROVAL: CatalystType.REGULATORY_APPROVAL,
    CatalystType.PHASE3_SUCCESS: CatalystType.REGULATORY_MILESTONE,
    CatalystType.MERGER: CatalystType.ACQUISITION,
    CatalystType.GUIDANCE_UPGRADE: CatalystType.MANAGEMENT_GUIDANCE,
    CatalystType.GUIDANCE_DOWNGRADE: CatalystType.MANAGEMENT_GUIDANCE,
    CatalystType.BULK_DEAL: CatalystType.INSTITUTIONAL_BUYING,
    CatalystType.BLOCK_DEAL: CatalystType.INSTITUTIONAL_BUYING,
}


class HybridCatalystClassifier:
    """Classifies catalyst with rules first; defers to LLM when confidence low."""

    def __init__(
        self,
        *,
        config: HybridCatalystConfig | None = None,
        analysis_service: CatalystAnalysisService | None = None,
        scoring_service: CatalystScoringService | None = None,
        headline_refinement: CatalystHeadlineRefinementService | None = None,
    ) -> None:
        self._config = config or HybridCatalystConfig()
        self._analysis = analysis_service or CatalystAnalysisService()
        self._scoring = scoring_service or CatalystScoringService()
        self._refinement = headline_refinement or CatalystHeadlineRefinementService(
            scoring_service=self._scoring
        )
        self._logger = structlog.get_logger(self.__class__.__name__)

    def classify_sentiment(
        self, sentiment: SentimentAnalysis, articles: list[Article]
    ) -> SentimentAnalysis:
        linked = self._linked_articles(sentiment, articles)
        text = self._combined_text(sentiment, linked)
        rule_type, rule_conf = self._rule_classify(text, linked)

        catalyst_type = sentiment.primary_catalyst_type
        confidence = sentiment.classification_confidence

        if rule_conf >= self._config.rule_confidence_skip_llm and rule_type is not None:
            catalyst_type = self._normalize(rule_type)
            confidence = rule_conf
        elif sentiment.llm_classified and sentiment.primary_catalyst_type != CatalystType.OTHER:
            catalyst_type = self._normalize(sentiment.primary_catalyst_type)
            confidence = max(confidence, 0.7)
        elif rule_type is not None:
            catalyst_type = self._normalize(rule_type)
            confidence = max(rule_conf, 0.5)

        updated = sentiment.model_copy(
            update={
                "primary_catalyst_type": catalyst_type,
                "classification_confidence": min(1.0, confidence),
                "catalyst_score": self._scoring.score_with_direct_news_cap(
                    catalyst_type,
                    direct_company_news=sentiment.direct_company_news,
                ),
            }
        )
        return self._refinement.refine(updated, linked)

    def _rule_classify(
        self, text: str, articles: list[Article]
    ) -> tuple[CatalystType | None, float]:
        if not articles:
            return self._headline_rules(text), 0.75 if self._headline_rules(text) else 0.3

        best = max(articles, key=lambda a: (a.catalyst_score, a.priority_score))
        headline_type = self._headline_rules(text)
        if headline_type:
            return headline_type, 0.9
        if best.catalyst_type != CatalystType.OTHER:
            return best.catalyst_type, 0.85
        return None, 0.3

    def _headline_rules(self, text: str) -> CatalystType | None:
        lower = text.lower()
        rules: list[tuple[str, CatalystType]] = [
            ("earnings miss", CatalystType.EARNINGS_MISS),
            ("beats estimate", CatalystType.EARNINGS_BEAT),
            ("guidance upgrade", CatalystType.GUIDANCE_UPGRADE),
            ("guidance cut", CatalystType.GUIDANCE_DOWNGRADE),
            ("broker downgrade", CatalystType.BROKER_DOWNGRADE),
            ("broker upgrade", CatalystType.BROKER_UPGRADE),
            ("block deal", CatalystType.BLOCK_DEAL),
            ("bulk deal", CatalystType.BULK_DEAL),
            ("promoter buying", CatalystType.PROMOTER_BUYING),
            ("promoter stake sale", CatalystType.PROMOTER_SELLING),
            ("phase 3", CatalystType.PHASE3_SUCCESS),
            ("fda approval", CatalystType.FDA_APPROVAL),
            ("index inclusion", CatalystType.INDEX_INCLUSION),
            ("index exclusion", CatalystType.INDEX_EXIT),
            ("defence order", CatalystType.DEFENCE_ORDER),
            ("merger", CatalystType.MERGER),
            ("sector headwind", CatalystType.SECTOR_HEADWIND),
        ]
        for phrase, ctype in rules:
            if phrase in lower:
                return ctype
        if re.search(r"\d+\s*crore", lower) and "order" in lower:
            return CatalystType.MAJOR_ORDER_WIN
        return None

    @staticmethod
    def _normalize(catalyst_type: CatalystType) -> CatalystType:
        return _ALIAS_MAP.get(catalyst_type, catalyst_type)

    @staticmethod
    def _linked_articles(
        sentiment: SentimentAnalysis, articles: list[Article]
    ) -> list[Article]:
        if not sentiment.article_ids:
            return []
        article_map = {a.id: a for a in articles}
        return [article_map[aid] for aid in sentiment.article_ids if aid in article_map]

    @staticmethod
    def _combined_text(sentiment: SentimentAnalysis, articles: list[Article]) -> str:
        chunks = [sentiment.primary_catalyst_summary or "", sentiment.reason or ""]
        chunks.extend(f"{a.title} {a.content[:400]}" for a in articles)
        return " ".join(chunks).lower()
