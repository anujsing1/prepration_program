"""Ranking strategy pattern implementations."""

from abc import ABC, abstractmethod

import structlog

from morning_trading_agent.application.ranking.candidate_build_result import CandidateBuildResult
from morning_trading_agent.config.premarket_config import RankingWeightConfig
from morning_trading_agent.domain.entities.article import (
    SentimentAnalysis,
    Stock,
    TradingCandidate,
)
from morning_trading_agent.domain.entities.explanation import ScoreBreakdown
from morning_trading_agent.domain.entities.technical import TechnicalAnalysisResult
from morning_trading_agent.domain.value_objects.sentiment import Score


class RankingStrategy(ABC):
    """Abstract ranking strategy."""

    @abstractmethod
    def build_candidates(
        self,
        stocks: list[Stock],
        sentiments: list[SentimentAnalysis],
        technicals: list[TechnicalAnalysisResult],
    ) -> CandidateBuildResult:
        """Build scored candidates for all joinable stocks (no truncation)."""

    @abstractmethod
    def sort_candidates(self, candidates: list[TradingCandidate]) -> list[TradingCandidate]:
        """Sort candidates by final score descending."""

    def rank(
        self,
        stocks: list[Stock],
        sentiments: list[SentimentAnalysis],
        technicals: list[TechnicalAnalysisResult],
        *,
        top_n: int | None = None,
    ) -> list[TradingCandidate]:
        """Build, sort, and optionally cap — prefer explicit build/filter/sort pipeline."""
        build_result = self.build_candidates(stocks, sentiments, technicals)
        sorted_candidates = self.sort_candidates(build_result.candidates)
        if top_n is not None:
            return sorted_candidates[:top_n]
        return sorted_candidates


class BaseRankingStrategy(RankingStrategy):
    """Shared logic for building and scoring candidates."""

    _score_logger = structlog.get_logger("ScoreForensics")

    def build_candidates(
        self,
        stocks: list[Stock],
        sentiments: list[SentimentAnalysis],
        technicals: list[TechnicalAnalysisResult],
    ) -> CandidateBuildResult:
        sentiment_map = {s.symbol: s for s in sentiments}
        technical_map = {t.symbol: t for t in technicals}
        candidates: list[TradingCandidate] = []
        dropped_missing_sentiment: list[str] = []
        dropped_missing_technical: list[str] = []

        for stock in stocks:
            sentiment = sentiment_map.get(stock.symbol)
            technical_result = technical_map.get(stock.symbol)
            if sentiment is None:
                dropped_missing_sentiment.append(stock.symbol)
                continue
            if technical_result is None:
                dropped_missing_technical.append(stock.symbol)
                continue

            news_score = Score.from_sentiment(sentiment.score).value
            technical_score = technical_result.technical_score
            confidence_score = sentiment.confidence * 100.0
            freshness_score = sentiment.freshness_score
            catalyst_score = sentiment.catalyst_score
            priority_score = sentiment.priority_score
            final_score, breakdown = self._compute_final_score(
                news_score,
                technical_score,
                confidence_score,
                freshness_score,
                catalyst_score,
                priority_score,
            )

            from morning_trading_agent.application.services.technical_analysis_service import (
                TechnicalAnalysisService,
            )

            tradability_score = (
                sentiment.catalyst_quality.tradability_score
                if sentiment.catalyst_quality
                else None
            )
            candidates.append(
                TradingCandidate(
                    stock=stock,
                    news_score=news_score,
                    technical_score=technical_score,
                    confidence_score=confidence_score,
                    freshness_score=freshness_score,
                    catalyst_score=catalyst_score,
                    priority_score=priority_score,
                    final_score=final_score,
                    tradability_score=tradability_score,
                    score_breakdown=breakdown,
                    sentiment=sentiment,
                    technical=TechnicalAnalysisService.to_legacy_analysis(technical_result),
                )
            )
            self._score_logger.info(
                "score_component_trace",
                symbol=stock.symbol,
                originating_service=self.__class__.__name__,
                news_score_source=sentiment.score,
                news_score_normalized=news_score,
                technical_score_source=technical_result.technical_score,
                technical_score_fallback=None,
                confidence_source=sentiment.confidence,
                confidence_default=None,
                freshness_source=sentiment.freshness_score,
                freshness_fallback=0.0 if not sentiment.freshness_score else None,
                catalyst_source=sentiment.catalyst_score,
                catalyst_default=50.0 if sentiment.catalyst_score == 50.0 else None,
                final_score=final_score,
                llm_provider=sentiment.llm_classified,
            )

        return CandidateBuildResult(
            candidates=candidates,
            dropped_missing_sentiment=dropped_missing_sentiment,
            dropped_missing_technical=dropped_missing_technical,
        )

    def sort_candidates(self, candidates: list[TradingCandidate]) -> list[TradingCandidate]:
        return sorted(candidates, key=lambda c: c.final_score, reverse=True)

    @abstractmethod
    def _compute_final_score(
        self,
        news_score: float,
        technical_score: float,
        confidence_score: float,
        freshness_score: float,
        catalyst_score: float,
        priority_score: float,
    ) -> tuple[float, ScoreBreakdown | None]:
        """Compute final score using strategy-specific weights."""


class PremarketHybridRankingStrategy(BaseRankingStrategy):
    """Pre-market ranking optimized for 07:00-09:15 IST monitoring."""

    def __init__(self, *, weight_config: RankingWeightConfig | None = None) -> None:
        self._weights = weight_config or RankingWeightConfig()
        self._weights.validate_weights()

    def _compute_final_score(
        self,
        news_score: float,
        technical_score: float,
        confidence_score: float,
        freshness_score: float,
        catalyst_score: float,
        priority_score: float,
    ) -> tuple[float, ScoreBreakdown]:
        w = self._weights
        final = (
            catalyst_score * w.catalyst
            + technical_score * w.technical
            + news_score * w.sentiment
            + confidence_score * w.confidence
            + freshness_score * w.freshness
            + priority_score * w.priority
        )
        breakdown = ScoreBreakdown(
            technical=technical_score,
            catalyst=catalyst_score,
            sentiment=news_score,
            confidence=confidence_score,
            freshness=freshness_score,
            priority=priority_score,
            final=round(final, 2),
        )
        return breakdown.final, breakdown


class HybridRankingStrategy(BaseRankingStrategy):
    """Default hybrid ranking with freshness and catalyst weighting."""

    def _compute_final_score(
        self,
        news_score: float,
        technical_score: float,
        confidence_score: float,
        freshness_score: float,
        catalyst_score: float,
        priority_score: float,
    ) -> tuple[float, ScoreBreakdown | None]:
        final = (
            news_score * 0.25
            + technical_score * 0.45
            + confidence_score * 0.12
            + freshness_score * 0.10
            + catalyst_score * 0.08
        )
        return round(final, 2), None


class NewsDrivenRankingStrategy(BaseRankingStrategy):
    """News-heavy ranking strategy."""

    def _compute_final_score(
        self,
        news_score: float,
        technical_score: float,
        confidence_score: float,
        freshness_score: float,
        catalyst_score: float,
        priority_score: float,
    ) -> tuple[float, ScoreBreakdown | None]:
        _ = priority_score
        final = (
            news_score * 0.45
            + technical_score * 0.20
            + confidence_score * 0.10
            + freshness_score * 0.15
            + catalyst_score * 0.10
        )
        return round(final, 2), None


class MomentumRankingStrategy(BaseRankingStrategy):
    """Technical momentum ranking strategy."""

    def _compute_final_score(
        self,
        news_score: float,
        technical_score: float,
        confidence_score: float,
        freshness_score: float,
        catalyst_score: float,
        priority_score: float,
    ) -> tuple[float, ScoreBreakdown | None]:
        _ = priority_score
        final = (
            news_score * 0.10
            + technical_score * 0.60
            + confidence_score * 0.10
            + freshness_score * 0.12
            + catalyst_score * 0.08
        )
        return round(final, 2), None
