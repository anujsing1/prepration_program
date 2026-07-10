"""Deterministic post-LLM catalyst reclassification from headlines."""

import structlog

from morning_trading_agent.application.services.catalyst.catalyst_scoring_service import (
    CatalystScoringService,
)
from morning_trading_agent.domain.entities.article import Article, SentimentAnalysis
from morning_trading_agent.domain.value_objects.catalyst import CatalystType

_REFINABLE_TYPES = frozenset(
    {
        CatalystType.OTHER,
        CatalystType.GENERAL_UPDATE,
        CatalystType.GENERIC_MENTION,
        CatalystType.EARNINGS,
        CatalystType.CORPORATE_COMMUNICATION,
        CatalystType.SECTOR_TAILWIND,
    }
)


class CatalystHeadlineRefinementService:
    """Refines weak LLM classifications using headline keyword rules."""

    def __init__(self, *, scoring_service: CatalystScoringService | None = None) -> None:
        self._scoring = scoring_service or CatalystScoringService()
        self._logger = structlog.get_logger(self.__class__.__name__)

    def refine(
        self,
        sentiment: SentimentAnalysis,
        articles: list[Article],
    ) -> SentimentAnalysis:
        """Return sentiment with refined catalyst type when headline rules match."""
        original = sentiment.primary_catalyst_type
        if original not in _REFINABLE_TYPES and sentiment.classification_confidence >= 0.75:
            return sentiment

        text = self._combined_text(sentiment, articles)
        new_type = self._classify_from_text(text)
        if new_type is None or new_type == original:
            confidence = sentiment.classification_confidence
            if new_type is None and original == CatalystType.OTHER:
                confidence = min(confidence, 0.35)
            return sentiment.model_copy(update={"classification_confidence": confidence})

        direct_news = sentiment.direct_company_news
        if new_type in {
            CatalystType.DEFENCE_PROCUREMENT,
            CatalystType.THEMATIC_DEMAND_SURGE,
            CatalystType.SECTOR_TAILWIND,
            CatalystType.POLICY_BENEFICIARY,
        }:
            direct_news = False
        elif new_type in {
            CatalystType.CLINICAL_TRIAL,
            CatalystType.REGULATORY_MILESTONE,
            CatalystType.ACQUISITION,
            CatalystType.ORDER_WIN,
            CatalystType.LARGE_CONTRACT,
        }:
            direct_news = True

        catalyst_score = self._scoring.score_with_direct_news_cap(
            new_type, direct_company_news=direct_news
        )

        self._logger.info(
            "catalyst_classified",
            symbol=sentiment.symbol,
            original_type=original.value,
            refined_type=new_type.value,
            confidence=0.9,
            article_title=self._primary_title(sentiment, articles)[:160],
        )

        return sentiment.model_copy(
            update={
                "primary_catalyst_type": new_type,
                "catalyst_score": catalyst_score,
                "direct_company_news": direct_news,
                "classification_confidence": 0.9,
                "llm_classified": True,
            }
        )

    def _classify_from_text(self, text: str) -> CatalystType | None:
        lower = text.lower()

        if any(
            kw in lower
            for kw in (
                "clinical trial",
                "phase 3",
                "phase iii",
                "phase 2",
                "phase ii",
                "safety review",
                "trial clearance",
                "fda approval",
                "drug approval",
            )
        ):
            if any(kw in lower for kw in ("phase 3", "phase iii", "on track", "cleared")):
                return CatalystType.REGULATORY_MILESTONE
            return CatalystType.CLINICAL_TRIAL

        if any(
            kw in lower
            for kw in (
                "defence",
                "defense",
                "drone",
                "procurement",
                "armed forces",
                "crore drone",
                "defence order",
            )
        ):
            if any(kw in lower for kw in ("crore", "procurement", "program", "buy")):
                return CatalystType.DEFENCE_PROCUREMENT
            return CatalystType.THEMATIC_DEMAND_SURGE

        if any(kw in lower for kw in ("joint venture", "jv with", "jv announcement", "j.v.")):
            return CatalystType.JV_ANNOUNCEMENT

        if any(
            kw in lower
            for kw in (
                "manufacturing expansion",
                "new plant",
                "capacity expansion",
                "factory expansion",
            )
        ):
            return CatalystType.MANUFACTURING_EXPANSION

        if any(kw in lower for kw in ("export opportunity", "export order", "export market")):
            return CatalystType.EXPORT_OPPORTUNITY

        if any(kw in lower for kw in ("policy beneficiary", "policy boost", "government policy")):
            return CatalystType.POLICY_BENEFICIARY

        if any(
            kw in lower
            for kw in (
                "shares rise",
                "shares jump",
                "stock jumps",
                "hits upper circuit",
                "strong growth outlook",
                "growth outlook",
            )
        ) and any(kw in lower for kw in ("sector", "jewellery", "defence", "pharma", "it stocks")):
            return CatalystType.SECTOR_TAILWIND

        if any(kw in lower for kw in ("order win", "wins order", "bagged order")):
            return CatalystType.ORDER_WIN

        if any(kw in lower for kw in ("major contract", "large contract", "contract worth", "crore contract")):
            return CatalystType.LARGE_CONTRACT

        if any(kw in lower for kw in ("acquisition", "acquires", "merger", "takeover")):
            return CatalystType.ACQUISITION

        if any(kw in lower for kw in ("regulatory approval", "regulatory milestone", "clearance granted")):
            return CatalystType.REGULATORY_MILESTONE

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
    def _primary_title(sentiment: SentimentAnalysis, articles: list[Article]) -> str:
        article_map = {a.id: a for a in articles}
        for article_id in sentiment.article_ids:
            article = article_map.get(article_id)
            if article:
                return article.title
        if articles:
            return articles[0].title
        return sentiment.primary_catalyst_summary[:160]
