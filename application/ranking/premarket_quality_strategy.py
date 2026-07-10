"""Pre-market ranking Formula V2 with magnitude, materiality, and tradability."""

from morning_trading_agent.application.ranking.candidate_build_result import CandidateBuildResult
from morning_trading_agent.application.ranking.strategies import BaseRankingStrategy
from morning_trading_agent.config.premarket_config import RankingWeightV2Config
from morning_trading_agent.domain.entities.article import (
    SentimentAnalysis,
    Stock,
    TradingCandidate,
)
from morning_trading_agent.domain.entities.explanation import ScoreBreakdown
from morning_trading_agent.domain.entities.technical import TechnicalAnalysisResult
from morning_trading_agent.domain.value_objects.sentiment import Score


class PremarketQualityRankingStrategy(BaseRankingStrategy):
    """Ranking V2: catalyst quality dimensions with configurable weights."""

    def __init__(self, *, weight_config: RankingWeightV2Config | None = None) -> None:
        self._weights = weight_config or RankingWeightV2Config()
        self._weights.validate_weights()

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

            quality = sentiment.catalyst_quality
            effective_catalyst = (
                quality.effective_catalyst_score if quality else sentiment.catalyst_score
            )
            magnitude_score = quality.magnitude_score if quality else 50.0
            materiality_score = quality.materiality_score if quality else 50.0
            tradability_score = quality.tradability_score if quality else 50.0
            liquidity_score = (
                technical_result.institutional_tradability_score or tradability_score
            )

            news_score = Score.from_sentiment(sentiment.score).value
            technical_score = technical_result.technical_score
            confidence_score = sentiment.confidence * 100.0

            final_score, breakdown = self._compute_v2_score(
                effective_catalyst=effective_catalyst,
                magnitude_score=magnitude_score,
                materiality_score=materiality_score,
                tradability_score=tradability_score,
                technical_score=technical_score,
                news_score=news_score,
                confidence_score=confidence_score,
            )

            from morning_trading_agent.application.services.technical_analysis_service import (
                TechnicalAnalysisService,
            )

            candidates.append(
                TradingCandidate(
                    stock=stock,
                    news_score=news_score,
                    technical_score=technical_score,
                    confidence_score=confidence_score,
                    freshness_score=sentiment.freshness_score,
                    catalyst_score=sentiment.catalyst_score,
                    effective_catalyst_score=effective_catalyst,
                    magnitude_score=magnitude_score,
                    materiality_score=materiality_score,
                    tradability_score=tradability_score,
                    liquidity_score=liquidity_score,
                    institutional_tradability_score=liquidity_score,
                    priority_score=sentiment.priority_score,
                    final_score=final_score,
                    score_breakdown=breakdown,
                    sentiment=sentiment,
                    technical=TechnicalAnalysisService.to_legacy_analysis(technical_result),
                )
            )

        return CandidateBuildResult(
            candidates=candidates,
            dropped_missing_sentiment=dropped_missing_sentiment,
            dropped_missing_technical=dropped_missing_technical,
        )

    def _compute_final_score(
        self,
        news_score: float,
        technical_score: float,
        confidence_score: float,
        freshness_score: float,
        catalyst_score: float,
        priority_score: float,
    ) -> tuple[float, ScoreBreakdown | None]:
        _ = freshness_score, priority_score
        return self._compute_v2_score(
            effective_catalyst=catalyst_score,
            magnitude_score=50.0,
            materiality_score=50.0,
            tradability_score=50.0,
            technical_score=technical_score,
            news_score=news_score,
            confidence_score=confidence_score,
        )

    def _compute_v2_score(
        self,
        *,
        effective_catalyst: float,
        magnitude_score: float,
        materiality_score: float,
        tradability_score: float,
        technical_score: float,
        news_score: float,
        confidence_score: float,
    ) -> tuple[float, ScoreBreakdown]:
        w = self._weights
        wc = effective_catalyst * w.catalyst
        wm = magnitude_score * w.magnitude
        wmat = materiality_score * w.materiality
        wtr = tradability_score * w.tradability
        wtech = technical_score * w.technical
        wsent = news_score * w.sentiment
        wconf = confidence_score * w.confidence
        final = wc + wm + wmat + wtr + wtech + wsent + wconf
        breakdown = ScoreBreakdown(
            technical=technical_score,
            catalyst=effective_catalyst,
            sentiment=news_score,
            confidence=confidence_score,
            magnitude=magnitude_score,
            materiality=materiality_score,
            tradability=tradability_score,
            final=round(final, 2),
            weighted_catalyst=round(wc, 2),
            weighted_magnitude=round(wm, 2),
            weighted_materiality=round(wmat, 2),
            weighted_tradability=round(wtr, 2),
            weighted_technical=round(wtech, 2),
            weighted_sentiment=round(wsent, 2),
            weighted_confidence=round(wconf, 2),
        )
        return breakdown.final, breakdown
