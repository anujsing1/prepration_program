"""Catalyst verification agent — additional OTHER refinement pass."""

import structlog

from morning_trading_agent.application.services.catalyst.catalyst_headline_refinement_service import (
    CatalystHeadlineRefinementService,
)
from morning_trading_agent.domain.entities.article import Article, SentimentAnalysis
from morning_trading_agent.domain.value_objects.catalyst import CatalystType


class CatalystVerificationAgent:
    """Second-pass headline refinement for remaining OTHER classifications."""

    def __init__(self) -> None:
        self._refinement = CatalystHeadlineRefinementService()
        self._logger = structlog.get_logger(self.__class__.__name__)

    def verify(
        self,
        sentiments: list[SentimentAnalysis],
        articles: list[Article],
    ) -> list[SentimentAnalysis]:
        """Apply extra headline refinement to OTHER classifications."""
        article_map = {article.id: article for article in articles}
        verified: list[SentimentAnalysis] = []
        other_before = sum(1 for s in sentiments if s.primary_catalyst_type == CatalystType.OTHER)

        for sentiment in sentiments:
            if sentiment.primary_catalyst_type != CatalystType.OTHER:
                verified.append(sentiment)
                continue
            linked = [
                article_map[aid] for aid in sentiment.article_ids if aid in article_map
            ]
            if not linked:
                verified.append(sentiment)
                continue
            verified.append(self._refinement.refine(sentiment, linked))

        other_after = sum(1 for s in verified if s.primary_catalyst_type == CatalystType.OTHER)
        self._logger.info(
            "catalyst_verification_complete",
            other_before=other_before,
            other_after=other_after,
            improved=max(0, other_before - other_after),
        )
        return verified
