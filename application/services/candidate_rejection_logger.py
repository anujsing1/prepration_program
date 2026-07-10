"""Structured logging for candidate rejections."""

import structlog

from morning_trading_agent.application.services.catalyst.catalyst_tier_service import (
    CatalystTierService,
)
from morning_trading_agent.domain.entities.article import TradingCandidate
from morning_trading_agent.domain.value_objects.catalyst_tier import CatalystTier


class CandidateRejectionLogger:
    """Emits rich rejection context for tuning."""

    def __init__(self, *, tier_service: CatalystTierService | None = None) -> None:
        self._tiers = tier_service or CatalystTierService()
        self._logger = structlog.get_logger("candidate_rejection")

    def log_rejection(
        self,
        candidate: TradingCandidate,
        reason: str,
        *,
        stage: str = "catalyst",
    ) -> None:
        sentiment = candidate.sentiment
        quality = sentiment.catalyst_quality
        tier = self._tiers.tier_for(sentiment.primary_catalyst_type)
        tradability = candidate.tradability_score or (
            quality.tradability_score if quality else None
        )
        materiality = candidate.materiality_score or (
            quality.materiality_score if quality else None
        )
        effective = candidate.effective_catalyst_score or candidate.catalyst_score

        self._logger.info(
            "candidate_rejected",
            stage=stage,
            symbol=candidate.stock.symbol,
            reason=reason,
            catalyst_type=sentiment.primary_catalyst_type.value,
            catalyst_score=round(candidate.catalyst_score, 1),
            effective_catalyst_score=round(effective, 1) if effective else None,
            technical_score=round(candidate.technical_score, 1),
            tradability_score=round(tradability, 1) if tradability is not None else None,
            materiality_score=round(materiality, 1) if materiality is not None else None,
            tier=tier.value,
            direct_company_news=sentiment.direct_company_news,
            selection_mode=candidate.selection_mode,
            article_title=(sentiment.primary_catalyst_summary or sentiment.reason)[:160],
        )

    def log_technical_override(
        self,
        candidate: TradingCandidate,
        *,
        effective_min_technical: float,
    ) -> None:
        self._logger.info(
            "catalyst_technical_override",
            symbol=candidate.stock.symbol,
            catalyst_type=candidate.sentiment.primary_catalyst_type.value,
            catalyst_score=round(candidate.catalyst_score, 1),
            technical_score=round(candidate.technical_score, 1),
            threshold=effective_min_technical,
            tier=CatalystTier.TIER_1.value,
        )
