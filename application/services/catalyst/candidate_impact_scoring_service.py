"""Composite candidate quality from impact dimensions."""

from __future__ import annotations

from morning_trading_agent.config.premarket_config import ImpactWeightConfig
from morning_trading_agent.domain.entities.article import SentimentAnalysis, TradingCandidate
from morning_trading_agent.domain.value_objects.catalyst_impact import CatalystImpactProfile


class CandidateImpactScoringService:
    """Computes composite impact quality; catalyst type is metadata only."""

    def __init__(self, *, weight_config: ImpactWeightConfig | None = None) -> None:
        self._weights = weight_config or ImpactWeightConfig()

    def composite_score(self, impact: CatalystImpactProfile) -> float:
        weights = self._weights.normalized()
        total = 0.0
        for name, score in impact.dimension_items():
            total += score * weights.get(name, 0.0)
        return round(min(100.0, max(0.0, total)), 2)

    def apply_penny_penalty(self, candidate: TradingCandidate, composite: float) -> float:
        close = candidate.technical.previous_close
        if close <= 0 or close >= 20.0:
            return composite
        penalty = self._weights.penny_stock_penalty
        return round(max(0.0, composite - penalty), 2)

    def score_sentiment(self, sentiment: SentimentAnalysis) -> tuple[CatalystImpactProfile, float]:
        impact = sentiment.catalyst_impact or CatalystImpactProfile()
        composite = self.composite_score(impact)
        return impact, composite

    def score_candidate(self, candidate: TradingCandidate) -> float:
        impact = candidate.sentiment.catalyst_impact or CatalystImpactProfile()
        composite = self.composite_score(impact)
        return self.apply_penny_penalty(candidate, composite)

    def dimension_contributions(
        self, impact: CatalystImpactProfile
    ) -> dict[str, float]:
        weights = self._weights.normalized()
        return {
            name: round(score * weights.get(name, 0.0), 2)
            for name, score in impact.dimension_items()
        }
