"""Hard eligibility rejects only (class A) — swing/retail penalty framework."""

from morning_trading_agent.application.services.catalyst.catalyst_tier_service import (
    CatalystTierService,
)
from morning_trading_agent.application.services.catalyst.catalyst_tradability_service import (
    CatalystTradabilityService,
)
from morning_trading_agent.config.premarket_config import (
    CatalystRejectionConfig,
    NonTradableCatalystConfig,
    TradingProfileConfig,
)
from morning_trading_agent.domain.entities.article import TradingCandidate
from morning_trading_agent.domain.value_objects.catalyst import CatalystType
from morning_trading_agent.domain.value_objects.catalyst_tier import CatalystTier


class CandidateEligibilityService:
    """Returns hard-reject reasons only; soft issues handled by penalties."""

    def __init__(
        self,
        *,
        profile: TradingProfileConfig,
        catalyst_config: CatalystRejectionConfig | None = None,
        non_tradable_config: NonTradableCatalystConfig | None = None,
        tier_service: CatalystTierService | None = None,
    ) -> None:
        self._profile = profile
        self._catalyst = catalyst_config or CatalystRejectionConfig(
            reject_bearish_for_long_watchlist=profile.reject_bearish_for_long_watchlist,
            min_tradability_for_indirect_news=profile.min_tradability_for_indirect_news,
        )
        self._non_tradable = non_tradable_config or NonTradableCatalystConfig()
        self._tiers = tier_service or CatalystTierService()

    def hard_reject_reason(self, candidate: TradingCandidate) -> str | None:
        """Class-A rejection only (impact-based path uses adaptive thresholds)."""
        inst = (
            candidate.institutional_tradability_score
            or candidate.liquidity_score
        )
        if inst is not None and inst < self._profile.liquidity_hard_reject_below:
            return "low_liquidity"
        return None
