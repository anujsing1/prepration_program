"""Scores day-trader relevance for pre-market catalysts."""

from morning_trading_agent.application.services.catalyst.catalyst_scoring_service import (
    CatalystScoringService,
)
from morning_trading_agent.config.premarket_config import (
    CatalystRejectionConfig,
    NonTradableCatalystConfig,
    TradabilityConfig,
)
from morning_trading_agent.domain.entities.article import SentimentAnalysis
from morning_trading_agent.domain.value_objects.catalyst_quality import CatalystMagnitude


class TradabilityService:
    """Would a day trader care about this catalyst tomorrow morning?"""

    def __init__(
        self,
        *,
        config: TradabilityConfig | None = None,
        non_tradable_config: NonTradableCatalystConfig | None = None,
        rejection_config: CatalystRejectionConfig | None = None,
        scoring_service: CatalystScoringService | None = None,
    ) -> None:
        self._config = config or TradabilityConfig()
        self._non_tradable = non_tradable_config or NonTradableCatalystConfig()
        self._rejection = rejection_config or CatalystRejectionConfig()
        self._scoring = scoring_service

    def score(
        self,
        sentiment: SentimentAnalysis,
        *,
        materiality_score: float,
        magnitude_score: float,
        magnitude: CatalystMagnitude,
    ) -> float:
        catalyst_type = sentiment.primary_catalyst_type
        if catalyst_type in self._non_tradable.non_tradable_types:
            if self._non_tradable.mode == "penalize":
                return self._non_tradable.penalized_tradability_score
            return self._config.non_tradable_cap

        type_prior = self._config.tradability_by_type.get(
            catalyst_type, self._config.default_tradability
        )
        if self._scoring is not None:
            db_weight = self._scoring.tradability_weight(catalyst_type)
            if db_weight is not None:
                type_prior = db_weight
        blended = (
            type_prior * (1.0 - self._config.materiality_weight - self._config.magnitude_weight)
            + materiality_score * self._config.materiality_weight
            + magnitude_score * self._config.magnitude_weight
        )

        if magnitude in {CatalystMagnitude.VERY_HIGH, CatalystMagnitude.HIGH}:
            blended = min(100.0, blended + 8.0)
        elif magnitude in {CatalystMagnitude.VERY_LOW, CatalystMagnitude.LOW}:
            blended = max(0.0, blended - 15.0)

        if not sentiment.direct_company_news:
            if sentiment.thematic_sector_catalyst:
                blended = max(blended, self._rejection.thematic_tradability_floor)
            else:
                blended = min(blended, 35.0)

        return round(max(0.0, min(100.0, blended)), 2)
