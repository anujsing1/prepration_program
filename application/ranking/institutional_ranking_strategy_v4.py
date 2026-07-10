"""Institutional ranking V4 — V3 plus bounded market context sector bonus."""

from morning_trading_agent.agents.market.market_context_agent import (
    MarketContextAgent,
    MarketContextFeatures,
)
from morning_trading_agent.application.ranking.candidate_build_result import CandidateBuildResult
from morning_trading_agent.application.ranking.institutional_ranking_strategy import (
    InstitutionalRankingStrategy,
)
from morning_trading_agent.domain.entities.article import (
    SentimentAnalysis,
    Stock,
    TradingCandidate,
)
from morning_trading_agent.domain.entities.technical import TechnicalAnalysisResult


class InstitutionalRankingStrategyV4(InstitutionalRankingStrategy):
    """V3 composite with explicit market-context sector bonus (max +5)."""

    def __init__(
        self,
        *,
        v3_strategy: InstitutionalRankingStrategy,
        market_features: MarketContextFeatures | None = None,
    ) -> None:
        super().__init__(
            weight_config=v3_strategy._weights,
            base_builder=v3_strategy._base,
            audit_weight_config=v3_strategy._audit_weights,
        )
        self._market_features = market_features or MarketContextFeatures()
        self._market_agent = MarketContextAgent()

    def set_market_features(self, features: MarketContextFeatures) -> None:
        """Inject market context features before candidate build."""
        self._market_features = features

    def build_candidates(
        self,
        stocks: list[Stock],
        sentiments: list[SentimentAnalysis],
        technicals: list[TechnicalAnalysisResult],
        *,
        symbol_weights: dict[str, float] | None = None,
        symbol_events: dict[str, str] | None = None,
    ) -> CandidateBuildResult:
        result = super().build_candidates(
            stocks,
            sentiments,
            technicals,
            symbol_weights=symbol_weights,
            symbol_events=symbol_events,
        )
        adjusted: list[TradingCandidate] = []
        for candidate in result.candidates:
            bonus = self._market_agent.sector_bonus(
                self._market_features,
                catalyst_type=candidate.primary_catalyst_type.value,
            )
            if bonus <= 0:
                adjusted.append(candidate)
                continue
            new_final = min(100.0, candidate.final_score + bonus)
            breakdown = candidate.score_breakdown
            if breakdown is not None:
                breakdown = breakdown.model_copy(
                    update={"final": new_final, "market_context_bonus": bonus}
                )
            adjusted.append(
                candidate.model_copy(
                    update={"final_score": new_final, "score_breakdown": breakdown}
                )
            )
        return CandidateBuildResult(
            candidates=adjusted,
            dropped_missing_sentiment=result.dropped_missing_sentiment,
            dropped_missing_technical=result.dropped_missing_technical,
        )
