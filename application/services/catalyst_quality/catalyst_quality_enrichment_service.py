"""Orchestrates magnitude, materiality, tradability, and effective catalyst scoring."""

from morning_trading_agent.application.services.catalyst_quality.catalyst_escalation_service import (
    CatalystEscalationService,
)
from morning_trading_agent.application.services.catalyst_quality.catalyst_magnitude_service import (
    CatalystMagnitudeService,
)
from morning_trading_agent.application.services.catalyst_quality.effective_catalyst_score_service import (
    EffectiveCatalystScoreService,
)
from morning_trading_agent.application.services.catalyst_quality.materiality_service import (
    MaterialityService,
)
from morning_trading_agent.application.services.catalyst.tradability_profile_service import (
    TradabilityProfileService,
)
from morning_trading_agent.application.services.catalyst_quality.tradability_service import (
    TradabilityService,
)
from morning_trading_agent.config.premarket_config import NonTradableCatalystConfig
from morning_trading_agent.domain.entities.article import Article, SentimentAnalysis
from morning_trading_agent.domain.value_objects.catalyst_quality import (
    CatalystMagnitude,
    CatalystQualityScores,
)


class CatalystQualityEnrichmentService:
    """Enriches sentiment rows with CatalystQualityScores."""

    def __init__(
        self,
        *,
        magnitude_service: CatalystMagnitudeService | None = None,
        materiality_service: MaterialityService | None = None,
        tradability_service: TradabilityService | None = None,
        effective_catalyst_service: EffectiveCatalystScoreService | None = None,
        escalation_service: CatalystEscalationService | None = None,
        non_tradable_config: NonTradableCatalystConfig | None = None,
        profile_service: TradabilityProfileService | None = None,
    ) -> None:
        self._non_tradable = non_tradable_config or NonTradableCatalystConfig()
        self._escalation = escalation_service or CatalystEscalationService()
        self._magnitude = magnitude_service or CatalystMagnitudeService()
        self._materiality = materiality_service or MaterialityService(
            non_tradable_config=self._non_tradable
        )
        self._tradability = tradability_service or TradabilityService(
            non_tradable_config=self._non_tradable
        )
        self._effective = effective_catalyst_service or EffectiveCatalystScoreService()
        self._profile_service = profile_service or TradabilityProfileService()

    def enrich(
        self,
        sentiments: list[SentimentAnalysis],
        articles: list[Article],
        *,
        llm_magnitudes: dict[str, CatalystMagnitude] | None = None,
        llm_values_crore: dict[str, float] | None = None,
        llm_strategic_importance: dict[str, str] | None = None,
    ) -> list[SentimentAnalysis]:
        """Return sentiments with catalyst_quality populated."""
        llm_magnitudes = llm_magnitudes or {}
        llm_values = llm_values_crore or {}
        llm_importance = llm_strategic_importance or {}
        enriched: list[SentimentAnalysis] = []

        for sentiment in sentiments:
            sentiment = self._escalation.apply(sentiment, articles)
            llm_mag = llm_magnitudes.get(sentiment.symbol)
            llm_val = llm_values.get(sentiment.symbol)
            importance = llm_importance.get(sentiment.symbol)

            magnitude, magnitude_score, value_crore, source = self._magnitude.evaluate(
                sentiment,
                articles,
                llm_magnitude=llm_mag,
                llm_value_crore=llm_val,
            )
            materiality_score = self._materiality.score(
                sentiment,
                magnitude=magnitude,
                magnitude_score=magnitude_score,
                financial_value_crore=value_crore,
                strategic_importance=importance,
            )
            tradability_score = self._tradability.score(
                sentiment,
                materiality_score=materiality_score,
                magnitude_score=magnitude_score,
                magnitude=magnitude,
            )

            if (
                sentiment.primary_catalyst_type in self._non_tradable.non_tradable_types
                and self._non_tradable.mode == "penalize"
            ):
                materiality_score = min(
                    materiality_score, self._non_tradable.penalized_materiality_score
                )
                tradability_score = min(
                    tradability_score, self._non_tradable.penalized_tradability_score
                )

            effective = self._effective.effective_score(sentiment, articles)

            quality = CatalystQualityScores(
                magnitude=magnitude,
                magnitude_score=magnitude_score,
                materiality_score=materiality_score,
                tradability_score=tradability_score,
                effective_catalyst_score=effective,
                financial_value_crore=value_crore,
                magnitude_source=source,
            )
            enriched_sentiment = sentiment.model_copy(update={"catalyst_quality": quality})
            profile = self._profile_service.build(enriched_sentiment, articles)
            enriched.append(
                enriched_sentiment.model_copy(update={"catalyst_tradability": profile})
            )

        return enriched
