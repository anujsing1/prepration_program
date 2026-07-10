"""Ranking V3: Event × Technical × Liquidity composite (single-pass build)."""

from morning_trading_agent.application.ranking.candidate_build_result import CandidateBuildResult
from morning_trading_agent.application.services.pipeline.score_safety import candidate_final_score
from morning_trading_agent.application.ranking.premarket_quality_strategy import (
    PremarketQualityRankingStrategy,
)
from morning_trading_agent.application.ranking.strategies import RankingStrategy
from morning_trading_agent.application.services.technical_analysis_service import (
    TechnicalAnalysisService,
)
from morning_trading_agent.config.premarket_config import RankingWeightV2Config, RankingWeightV3Config
from morning_trading_agent.domain.entities.article import (
    SentimentAnalysis,
    Stock,
    TradingCandidate,
)
from morning_trading_agent.domain.entities.explanation import ScoreBreakdown
from morning_trading_agent.domain.entities.technical import TechnicalAnalysisResult
from morning_trading_agent.domain.value_objects.sentiment import Score, SentimentDirection


class InstitutionalRankingStrategy(RankingStrategy):
    """Institutional final composite using event, technical, and liquidity pillars."""

    def __init__(
        self,
        *,
        weight_config: RankingWeightV3Config | None = None,
        base_builder: PremarketQualityRankingStrategy | None = None,
        audit_weight_config: RankingWeightV2Config | None = None,
    ) -> None:
        self._weights = weight_config or RankingWeightV3Config()
        self._weights.validate_weights()
        self._base = base_builder or PremarketQualityRankingStrategy()
        self._audit_weights = audit_weight_config or RankingWeightV2Config()

    def build_candidates(
        self,
        stocks: list[Stock],
        sentiments: list[SentimentAnalysis],
        technicals: list[TechnicalAnalysisResult],
        *,
        symbol_weights: dict[str, float] | None = None,
        symbol_events: dict[str, str] | None = None,
    ) -> CandidateBuildResult:
        """Single-pass V3 scoring without intermediate V2 final_score."""
        sentiment_map = {s.symbol: s for s in sentiments}
        technical_map = {t.symbol: t for t in technicals}
        weights = symbol_weights or {}
        events = symbol_events or {}
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
                sentiment.composite_impact_score
                if sentiment.composite_impact_score is not None
                else (
                    quality.effective_catalyst_score if quality else sentiment.catalyst_score
                )
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
            weight = weights.get(stock.symbol, 1.0)

            candidate = TradingCandidate(
                stock=stock,
                news_score=news_score,
                technical_score=technical_score,
                confidence_score=confidence_score,
                freshness_score=sentiment.freshness_score,
                catalyst_score=sentiment.catalyst_score,
                effective_catalyst_score=effective_catalyst,
                composite_impact_score=sentiment.composite_impact_score,
                magnitude_score=magnitude_score,
                materiality_score=materiality_score,
                tradability_score=tradability_score,
                liquidity_score=liquidity_score,
                institutional_tradability_score=liquidity_score,
                priority_score=sentiment.priority_score,
                final_score=0.0,
                sentiment=sentiment,
                technical=TechnicalAnalysisService.to_legacy_analysis(technical_result),
                beneficiary_weight=weight,
                event_id=events.get(stock.symbol),
            )
            event_score = self._event_score(candidate)
            final = (
                self._weights.event * event_score
                + self._weights.technical * technical_score
                + self._weights.liquidity * liquidity_score
                + self._weights.sentiment * news_score
                + self._weights.freshness * candidate.freshness_score
            )
            final = min(100.0, final * (0.85 + 0.15 * weight))
            final *= self._direction_factor(sentiment.direction)

            w = self._weights
            audit = self._audit_weights
            breakdown = ScoreBreakdown(
                technical=technical_score,
                catalyst=event_score,
                sentiment=news_score,
                confidence=confidence_score,
                freshness=candidate.freshness_score,
                priority=liquidity_score,
                tradability=liquidity_score,
                magnitude=magnitude_score,
                materiality=materiality_score,
                final=round(final, 2),
                weighted_catalyst=round(event_score * w.event, 2),
                weighted_technical=round(technical_score * w.technical, 2),
                weighted_tradability=round(liquidity_score * w.liquidity, 2),
                weighted_sentiment=round(news_score * w.sentiment, 2),
                weighted_magnitude=round(magnitude_score * audit.magnitude, 2),
                weighted_materiality=round(materiality_score * audit.materiality, 2),
                weighted_confidence=0.0,
            )
            candidates.append(
                candidate.model_copy(
                    update={
                        "event_score": event_score,
                        "final_score": final,
                        "score_breakdown": breakdown,
                    }
                )
            )

        return CandidateBuildResult(
            candidates=candidates,
            dropped_missing_sentiment=dropped_missing_sentiment,
            dropped_missing_technical=dropped_missing_technical,
        )

    @staticmethod
    def _direction_factor(direction: SentimentDirection) -> float:
        return {
            SentimentDirection.BULLISH: 1.0,
            SentimentDirection.NEUTRAL: 0.85,
            SentimentDirection.BEARISH: 0.5,
        }[direction]

    @staticmethod
    def _event_score(candidate: TradingCandidate) -> float:
        quality = candidate.sentiment.catalyst_quality
        catalyst = candidate.effective_catalyst_score or candidate.catalyst_score
        magnitude = candidate.magnitude_score or (quality.magnitude_score if quality else 50.0)
        materiality = candidate.materiality_score or (
            quality.materiality_score if quality else 50.0
        )
        confidence = (candidate.sentiment.classification_confidence or 0.7) * 100.0
        return 0.35 * catalyst + 0.25 * materiality + 0.20 * magnitude + 0.20 * confidence

    def sort_candidates(self, candidates: list[TradingCandidate]) -> list[TradingCandidate]:
        return sorted(candidates, key=candidate_final_score, reverse=True)

    def select_top(self, candidates: list[TradingCandidate], n: int) -> list[TradingCandidate]:
        return self.sort_candidates(candidates)[:n]

    def score_sentiment(self, sentiment: SentimentAnalysis) -> Score:
        return self._base.score_sentiment(sentiment)
