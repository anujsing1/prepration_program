"""Composed candidate filtering: catalyst rules + watchlist quality."""

import structlog

from morning_trading_agent.application.services.candidate_filter_result import (
    CandidateFilterResult,
)
from morning_trading_agent.application.services.candidate_rejection_logger import (
    CandidateRejectionLogger,
)
from morning_trading_agent.application.services.catalyst.catalyst_tier_service import (
    CatalystTierService,
)
from morning_trading_agent.application.services.catalyst.catalyst_tradability_service import (
    CatalystTradabilityService,
)
from morning_trading_agent.application.services.watchlist_quality_filter import (
    WatchlistQualityFilterService,
)
from morning_trading_agent.config.premarket_config import (
    CatalystRejectionConfig,
    FilterRelaxationOverlay,
    NonTradableCatalystConfig,
)
from morning_trading_agent.domain.entities.article import TradingCandidate
from morning_trading_agent.domain.value_objects.catalyst import CatalystType
from morning_trading_agent.domain.value_objects.catalyst_tier import CatalystTier
from morning_trading_agent.domain.value_objects.sentiment import SentimentDirection


class CandidateFilterService:
    """Applies catalyst rejection rules then watchlist quality filters."""

    def __init__(
        self,
        *,
        quality_filter: WatchlistQualityFilterService,
        catalyst_config: CatalystRejectionConfig | None = None,
        non_tradable_config: NonTradableCatalystConfig | None = None,
        tier_service: CatalystTierService | None = None,
        rejection_logger: CandidateRejectionLogger | None = None,
    ) -> None:
        self._quality_filter = quality_filter
        self._catalyst_config = catalyst_config or CatalystRejectionConfig()
        self._non_tradable = non_tradable_config or NonTradableCatalystConfig()
        self._tiers = tier_service or CatalystTierService()
        self._rejection_log = rejection_logger or CandidateRejectionLogger(
            tier_service=self._tiers
        )
        self._logger = structlog.get_logger(self.__class__.__name__)

    def filter(
        self, candidates: list[TradingCandidate]
    ) -> tuple[list[TradingCandidate], list[TradingCandidate]]:
        """Return accepted and rejected candidates (backward compatible)."""
        result = self.filter_with_result(candidates)
        return result.accepted, result.rejected

    def filter_with_result(
        self,
        candidates: list[TradingCandidate],
        *,
        overlay: FilterRelaxationOverlay | None = None,
    ) -> CandidateFilterResult:
        """Return accepted/rejected candidates with per-reason counts."""
        result = CandidateFilterResult()
        catalyst_accepted: list[TradingCandidate] = []

        for candidate in candidates:
            reason = self._catalyst_rejection_reason(candidate, overlay=overlay)
            if reason:
                result.rejected.append(candidate)
                result.record_rejection(candidate, reason)
                self._rejection_log.log_rejection(candidate, reason, stage="catalyst")
            else:
                catalyst_accepted.append(candidate)

        quality_result = self._quality_filter.filter_with_result(catalyst_accepted)
        result.accepted = quality_result.accepted
        result.rejected.extend(quality_result.rejected)
        for reason, count in quality_result.rejection_counts.items():
            result.rejection_counts[reason] = result.rejection_counts.get(reason, 0) + count
        result.rejection_reasons.update(quality_result.rejection_reasons)

        self._logger.info(
            "candidate_filter_complete",
            accepted=len(result.accepted),
            rejected=len(result.rejected),
            rejection_counts=result.rejection_counts,
        )
        return result

    def _effective_min_technical(
        self, candidate: TradingCandidate, tier: CatalystTier
    ) -> float:
        cfg = self._catalyst_config
        sentiment = candidate.sentiment
        if (
            tier == CatalystTier.TIER_1
            and sentiment.direct_company_news
            and candidate.catalyst_score >= cfg.tier1_technical_override_min_catalyst
        ):
            self._rejection_log.log_technical_override(
                candidate,
                effective_min_technical=cfg.tier1_technical_override_min_technical,
            )
            return cfg.tier1_technical_override_min_technical
        return cfg.min_technical_score

    def _catalyst_rejection_reason(
        self,
        candidate: TradingCandidate,
        *,
        overlay: FilterRelaxationOverlay | None = None,
    ) -> str | None:
        profile_reason = self._tradability_rejection_reason(candidate)
        if profile_reason:
            return profile_reason

        if overlay and overlay.technical_rescue_min is not None:
            if candidate.technical_score >= overlay.technical_rescue_min:
                return None

        if overlay and overlay.min_freshness_override is not None:
            if candidate.freshness_score < overlay.min_freshness_override:
                return "freshness_below_threshold"

        cfg = self._catalyst_config
        sentiment = candidate.sentiment
        catalyst_type = sentiment.primary_catalyst_type
        tier = self._tiers.tier_for(catalyst_type)

        reject_weak_catalyst_types = cfg.reject_weak_catalyst_types
        if overlay and overlay.allow_secondary_catalysts:
            reject_weak_catalyst_types = False

        if cfg.reject_bearish_for_long_watchlist and sentiment.direction == SentimentDirection.BEARISH:
            return "bearish_long_watchlist"

        if (
            cfg.reject_neutral_low_conviction
            and sentiment.direction == SentimentDirection.NEUTRAL
            and candidate.news_score < 45
        ):
            return "neutral_low_conviction"

        if catalyst_type in {
            CatalystType.EXCHANGE_CLARIFICATION,
            CatalystType.COMPLIANCE_FILING,
        }:
            return "exchange_or_compliance_noise"

        if (
            self._non_tradable.mode == "reject"
            and catalyst_type in self._non_tradable.non_tradable_types
        ):
            return "non_tradable_catalyst"

        if reject_weak_catalyst_types and self._tiers.is_weak_type_for_tier(
            catalyst_type, tier
        ):
            if tier == CatalystTier.TIER_2:
                if candidate.catalyst_score < cfg.tier2_min_catalyst_score:
                    return "weak_catalyst_type"
                if (
                    candidate.technical_score < cfg.tier2_min_technical_score
                    and candidate.news_score < cfg.tier2_min_sentiment_score
                ):
                    return "weak_tier2_signals"
            else:
                return "weak_catalyst_type"

        quality = candidate.sentiment.catalyst_quality
        tradability = candidate.tradability_score or (
            quality.tradability_score if quality else None
        )
        materiality = candidate.materiality_score or (
            quality.materiality_score if quality else None
        )

        if not candidate.sentiment.direct_company_news and tradability is not None:
            if tradability < cfg.min_tradability_for_indirect_news:
                return "no_direct_tradable_catalyst"

        if cfg.min_tradability_score is not None and tradability is not None:
            if tradability < cfg.min_tradability_score:
                return "low_tradability_score"
        if cfg.min_materiality_score is not None and materiality is not None:
            if materiality < cfg.min_materiality_score:
                return "low_materiality_score"

        effective = candidate.effective_catalyst_score or candidate.catalyst_score
        if tier == CatalystTier.TIER_3 and effective < cfg.tier3_min_effective_catalyst:
            return "weak_catalyst_type"

        if effective < cfg.min_catalyst_score:
            return "low_catalyst_score"

        if (
            not candidate.sentiment.direct_company_news
            and effective < cfg.min_catalyst_score_without_direct_news
        ):
            if candidate.sentiment.thematic_sector_catalyst:
                if (
                    tradability is not None
                    and tradability >= cfg.thematic_tradability_floor
                    and materiality is not None
                    and materiality >= cfg.thematic_materiality_floor
                ):
                    pass
                else:
                    return "weak_catalyst_without_direct_news"
            else:
                return "weak_catalyst_without_direct_news"

        min_technical = self._effective_min_technical(candidate, tier)
        if candidate.technical_score < min_technical:
            return "weak_technical_score"

        return None

    @staticmethod
    def _tradability_rejection_reason(candidate: TradingCandidate) -> str | None:
        profile = candidate.sentiment.catalyst_tradability
        reason = CatalystTradabilityService.filter_reason(profile)
        if reason:
            return reason
        if CatalystTradabilityService.blocked_reason_text(candidate):
            return "non_tradable_catalyst"
        return None
