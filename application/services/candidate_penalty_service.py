"""Soft penalty multipliers for ranked survivors (class B)."""

from dataclasses import dataclass, field

from morning_trading_agent.application.services.catalyst.catalyst_tier_service import (
    CatalystTierService,
)
from morning_trading_agent.config.premarket_config import (
    CatalystRejectionConfig,
    TradingProfileConfig,
)
from morning_trading_agent.domain.entities.article import TradingCandidate
from morning_trading_agent.domain.value_objects.catalyst import CatalystType
from morning_trading_agent.domain.value_objects.catalyst_tier import CatalystTier
from morning_trading_agent.domain.value_objects.pipeline_selection import (
    CatalystTradabilityClass,
)
from morning_trading_agent.domain.value_objects.sentiment import SentimentDirection


@dataclass
class PenaltyResult:
    """Penalty breakdown for one candidate."""

    multiplier: float = 1.0
    reasons: list[str] = field(default_factory=list)
    tradability_class: CatalystTradabilityClass = CatalystTradabilityClass.TRADABLE


class CandidatePenaltyService:
    """Applies profile-aware soft penalties; does not reject."""

    def __init__(
        self,
        *,
        profile: TradingProfileConfig,
        catalyst_config: CatalystRejectionConfig | None = None,
        tier_service: CatalystTierService | None = None,
    ) -> None:
        self._profile = profile
        self._penalties = profile.penalties
        self._catalyst = catalyst_config or CatalystRejectionConfig(
            min_tradability_for_indirect_news=profile.min_tradability_for_indirect_news,
        )
        self._tiers = tier_service or CatalystTierService()

    def compute(self, candidate: TradingCandidate) -> PenaltyResult:
        result = PenaltyResult()
        sentiment = candidate.sentiment
        catalyst_type = sentiment.primary_catalyst_type
        tier = self._tiers.tier_for(catalyst_type)
        result.tradability_class = self._tradability_class(tier, catalyst_type)

        direction = sentiment.direction
        if direction == SentimentDirection.BEARISH:
            self._apply(result, self._penalties.bearish_long_penalty, "bearish_long_penalty")
        elif direction == SentimentDirection.NEUTRAL:
            self._apply(result, self._penalties.neutral_penalty, "neutral_penalty")

        if not sentiment.direct_company_news:
            tradability = candidate.tradability_score or 50.0
            if tradability < self._catalyst.min_tradability_for_indirect_news:
                self._apply(result, self._penalties.indirect_catalyst_penalty, "indirect_catalyst")

        effective = candidate.effective_catalyst_score or candidate.catalyst_score
        if tier == CatalystTier.TIER_3 and effective < 40.0:
            self._apply(result, self._penalties.tier3_mid_catalyst_penalty, "tier3_weak_catalyst")

        if self._tiers.is_weak_type_for_tier(catalyst_type, tier) and tier == CatalystTier.TIER_2:
            if (
                candidate.technical_score < self._catalyst.tier2_min_technical_score
                and candidate.news_score < self._catalyst.tier2_min_sentiment_score
            ):
                self._apply(result, self._penalties.weak_tier2_penalty, "weak_tier2_signals")

        if candidate.technical_score < 55.0:
            factor = (
                self._penalties.weak_technical_low_penalty
                if candidate.technical_score < 40.0
                else self._penalties.weak_technical_mid_penalty
            )
            self._apply(result, factor, "weak_technical_penalty")

        if candidate.news_score < 40.0:
            self._apply(result, self._penalties.weak_sentiment_penalty, "weak_sentiment")

        inst = candidate.institutional_tradability_score or candidate.liquidity_score
        if inst is not None and inst < self._profile.min_inst_tradability:
            self._apply(result, self._penalties.liquidity_soft_penalty, "liquidity_soft_penalty")

        if (
            self._catalyst.reject_neutral_low_conviction
            and direction == SentimentDirection.NEUTRAL
            and candidate.news_score < 45
        ):
            self._apply(result, self._penalties.weak_sentiment_penalty, "neutral_low_conviction")

        return result

    @staticmethod
    def _apply(result: PenaltyResult, factor: float, reason: str) -> None:
        result.multiplier *= factor
        result.reasons.append(reason)

    @staticmethod
    def _tradability_class(tier: CatalystTier, catalyst_type: CatalystType) -> CatalystTradabilityClass:
        if tier == CatalystTier.TIER_1:
            return CatalystTradabilityClass.TRADABLE
        if tier == CatalystTier.TIER_2:
            return CatalystTradabilityClass.SUPPORTING
        if catalyst_type in {
            CatalystType.INVESTOR_MEETING,
            CatalystType.CORPORATE_COMMUNICATION,
            CatalystType.BOARD_MEETING,
        }:
            return CatalystTradabilityClass.NON_TRADABLE
        return CatalystTradabilityClass.NON_TRADABLE
