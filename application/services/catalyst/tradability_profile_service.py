"""Build canonical catalyst_tradability profiles from quality scores and policy."""

from __future__ import annotations

import structlog

from morning_trading_agent.application.services.catalyst.catalyst_tradability_service import (
    CatalystTradabilityService,
)
from morning_trading_agent.domain.entities.article import Article, SentimentAnalysis
from morning_trading_agent.domain.value_objects.catalyst_tradability import CatalystTradabilityProfile


class TradabilityProfileService:
    """Synthesizes policy (tradable/category) with canonical numeric tradability."""

    def __init__(
        self,
        tradability: CatalystTradabilityService | None = None,
    ) -> None:
        self._tradability = tradability or CatalystTradabilityService()
        self._logger = structlog.get_logger(self.__class__.__name__)

    def build(
        self,
        sentiment: SentimentAnalysis,
        articles: list[Article],
    ) -> CatalystTradabilityProfile:
        quality = sentiment.catalyst_quality
        if quality is None:
            msg = (
                f"catalyst_quality required before tradability profile build "
                f"for {sentiment.symbol}"
            )
            raise ValueError(msg)

        score = quality.tradability_score
        policy = self._tradability.assess(sentiment, articles)
        profile = policy.model_copy(update={"tradability_score": score})
        self._logger.debug(
            "tradability_profile_built",
            symbol=sentiment.symbol,
            tradability_score=score,
            tradable=profile.tradable,
            category=profile.category.value,
        )
        return profile
