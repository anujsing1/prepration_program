"""Resolves catalyst tier for filter policy."""

from morning_trading_agent.config.premarket_config import CatalystTierConfig
from morning_trading_agent.domain.value_objects.catalyst import CatalystType
from morning_trading_agent.domain.value_objects.catalyst_tier import (
    CatalystTier,
    DEFAULT_TIER_1_TYPES,
    DEFAULT_TIER_2_TYPES,
    DEFAULT_TIER_3_TYPES,
)


class CatalystTierService:
    """Maps catalyst types to TIER_1 / TIER_2 / TIER_3."""

    def __init__(self, *, config: CatalystTierConfig | None = None) -> None:
        self._config = config or CatalystTierConfig()

    def tier_for(self, catalyst_type: CatalystType) -> CatalystTier:
        if catalyst_type in self._config.tier_1_types:
            return CatalystTier.TIER_1
        if catalyst_type in self._config.tier_2_types:
            return CatalystTier.TIER_2
        if catalyst_type in self._config.tier_3_types:
            return CatalystTier.TIER_3
        return CatalystTier.TIER_3

    def is_weak_type_for_tier(self, catalyst_type: CatalystType, tier: CatalystTier) -> bool:
        """Whether weak_catalyst_type rejection applies."""
        if tier == CatalystTier.TIER_1:
            return False
        if tier == CatalystTier.TIER_2:
            return catalyst_type in self._config.tier_2_weak_types
        return catalyst_type in self._config.tier_3_types or catalyst_type == CatalystType.OTHER
