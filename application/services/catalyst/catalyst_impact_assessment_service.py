"""Assess catalyst impact dimensions without category-based rejection."""

from __future__ import annotations

import structlog

from morning_trading_agent.application.services.catalyst.candidate_impact_scoring_service import (
    CandidateImpactScoringService,
)
from morning_trading_agent.application.services.catalyst.catalyst_type_stats_service import (
    CatalystTypeStatsService,
)
from morning_trading_agent.domain.entities.article import Article, SentimentAnalysis
from morning_trading_agent.domain.value_objects.catalyst import CatalystType
from morning_trading_agent.domain.value_objects.catalyst_impact import CatalystImpactProfile
from morning_trading_agent.domain.value_objects.catalyst_quality import CatalystMagnitude
from morning_trading_agent.domain.value_objects.catalyst_tradability import (
    AcceptedCatalystDiagnostic,
)
from morning_trading_agent.domain.value_objects.sentiment import SentimentDirection


class CatalystImpactAssessmentService:
    """Computes impact profile and composite score; catalyst type is metadata only."""

    _EARNINGS_KEYWORDS = ("earnings", "results", "profit", "revenue", "guidance", "ebitda")
    _BALANCE_SHEET_KEYWORDS = ("debt", "fund raise", "buyback", "equity", "loan", "repayment")
    _VALUATION_KEYWORDS = ("valuation", "re-rating", "target price", "upgrade", "downgrade")

    def __init__(
        self,
        *,
        impact_scoring: CandidateImpactScoringService | None = None,
        stats_service: CatalystTypeStatsService | None = None,
    ) -> None:
        self._scoring = impact_scoring or CandidateImpactScoringService()
        self._stats = stats_service
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def assess(
        self,
        sentiment: SentimentAnalysis,
        articles: list[Article],
    ) -> SentimentAnalysis:
        impact = sentiment.catalyst_impact or self._heuristic_impact(sentiment, articles)
        composite = self._scoring.composite_score(impact)
        catalyst_code = self._catalyst_code(sentiment)
        if self._stats is not None:
            await self._stats.record_classification(catalyst_code)

        return sentiment.model_copy(
            update={
                "catalyst_impact": impact,
                "composite_impact_score": composite,
            }
        )

    def to_accepted_diagnostic(self, sentiment: SentimentAnalysis) -> AcceptedCatalystDiagnostic:
        impact = sentiment.catalyst_impact or CatalystImpactProfile()
        score = (
            sentiment.catalyst_quality.tradability_score
            if sentiment.catalyst_quality
            else impact.tradability
        )
        return AcceptedCatalystDiagnostic(
            symbol=sentiment.symbol,
            catalyst_type=sentiment.primary_catalyst_type.value,
            tradability_score=score,
        )

    def _heuristic_impact(
        self,
        sentiment: SentimentAnalysis,
        articles: list[Article],
    ) -> CatalystImpactProfile:
        text = self._combined_text(sentiment, articles).lower()
        magnitude = sentiment.llm_catalyst_magnitude or CatalystMagnitude.MEDIUM
        magnitude_score = self._magnitude_score(magnitude)
        value_crore = sentiment.llm_estimated_value_crore
        confidence = sentiment.classification_confidence * 100.0
        freshness = sentiment.freshness_score
        direct_news = sentiment.direct_company_news

        revenue = magnitude_score
        if value_crore is not None:
            if value_crore >= 100:
                revenue = min(100.0, revenue + 25.0)
            elif value_crore >= 25:
                revenue = min(100.0, revenue + 15.0)
            elif value_crore < 5:
                revenue = max(0.0, revenue - 20.0)

        earnings = magnitude_score
        if any(keyword in text for keyword in self._EARNINGS_KEYWORDS):
            earnings = min(100.0, earnings + 20.0)
        elif sentiment.primary_catalyst_type in {
            CatalystType.EARNINGS,
            CatalystType.EARNINGS_BEAT,
            CatalystType.EARNINGS_MISS,
        }:
            earnings = min(100.0, magnitude_score + 10.0)

        balance_sheet = magnitude_score * 0.7
        if any(keyword in text for keyword in self._BALANCE_SHEET_KEYWORDS):
            balance_sheet = min(100.0, magnitude_score + 15.0)

        valuation = (sentiment.catalyst_score + magnitude_score) / 2.0
        if any(keyword in text for keyword in self._VALUATION_KEYWORDS):
            valuation = min(100.0, valuation + 15.0)

        institutional = min(100.0, (magnitude_score * 0.5) + (confidence * 0.5))
        if sentiment.direction == SentimentDirection.BULLISH:
            institutional = min(100.0, institutional + 5.0)

        urgency = min(100.0, (freshness * 0.6) + (magnitude_score * 0.4))
        if magnitude in {CatalystMagnitude.VERY_HIGH, CatalystMagnitude.HIGH}:
            urgency = min(100.0, urgency + 10.0)

        tradability = magnitude_score
        if not direct_news:
            tradability = max(0.0, tradability - 25.0)
        if sentiment.thematic_sector_catalyst:
            tradability = max(tradability, 45.0)
        tradability = min(100.0, tradability)

        return CatalystImpactProfile(
            revenue_impact=round(revenue, 2),
            earnings_impact=round(earnings, 2),
            balance_sheet_impact=round(balance_sheet, 2),
            valuation_impact=round(valuation, 2),
            institutional_relevance=round(institutional, 2),
            urgency=round(urgency, 2),
            tradability=round(tradability, 2),
        )

    @staticmethod
    def _magnitude_score(magnitude: CatalystMagnitude) -> float:
        return {
            CatalystMagnitude.VERY_HIGH: 95.0,
            CatalystMagnitude.HIGH: 80.0,
            CatalystMagnitude.MEDIUM: 55.0,
            CatalystMagnitude.LOW: 35.0,
            CatalystMagnitude.VERY_LOW: 20.0,
        }[magnitude]

    @staticmethod
    def _catalyst_code(sentiment: SentimentAnalysis) -> str:
        if sentiment.proposed_catalyst_code:
            return sentiment.proposed_catalyst_code.upper()
        return sentiment.primary_catalyst_type.value.upper()

    @staticmethod
    def _combined_text(sentiment: SentimentAnalysis, articles: list[Article]) -> str:
        parts = [sentiment.primary_catalyst_summary, sentiment.reason]
        article_map = {article.id: article for article in articles}
        for article_id in sentiment.article_ids:
            article = article_map.get(article_id)
            if article:
                parts.append(f"{article.title} {article.content}")
        return " ".join(part for part in parts if part)
