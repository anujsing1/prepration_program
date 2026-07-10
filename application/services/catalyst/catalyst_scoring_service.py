"""Deterministic catalyst score lookup — Python only, no LLM."""

from morning_trading_agent.application.services.catalyst.catalyst_taxonomy_cache import (
    CatalystTaxonomyCache,
)
from morning_trading_agent.config.premarket_config import CatalystScoreConfig
from morning_trading_agent.domain.value_objects.catalyst import WEAK_CATALYST_TYPES, CatalystType
from morning_trading_agent.domain.value_objects.catalyst_codes import WEAK_TRADABILITY_THRESHOLD
from morning_trading_agent.domain.value_objects.sentiment import SentimentDirection

_BEARISH_DIRECTIONS = frozenset({SentimentDirection.BEARISH})


class CatalystScoringService:
    """Maps catalyst types to 0-100 scores from configuration or DB taxonomy."""

    def __init__(
        self,
        *,
        score_config: CatalystScoreConfig | None = None,
        taxonomy_cache: CatalystTaxonomyCache | None = None,
        use_db_taxonomy: bool = False,
    ) -> None:
        self._score_config = score_config or CatalystScoreConfig()
        self._taxonomy_cache = taxonomy_cache
        self._use_db_taxonomy = use_db_taxonomy

    def score(
        self,
        catalyst_type: CatalystType | str,
        *,
        direction: SentimentDirection | None = None,
    ) -> float:
        """Return configured score for a catalyst type."""
        code = catalyst_type.value if isinstance(catalyst_type, CatalystType) else str(catalyst_type)
        if self._use_db_taxonomy and self._taxonomy_cache is not None:
            entry = self._taxonomy_cache.get_by_code(code)
            if entry is not None:
                if direction in _BEARISH_DIRECTIONS:
                    return float(entry.bearish_weight)
                return float(entry.bullish_weight)
            other = self._taxonomy_cache.get_by_code("OTHER")
            if other is not None:
                return float(other.bullish_weight)
        enum_type = catalyst_type if isinstance(catalyst_type, CatalystType) else None
        if enum_type is None:
            try:
                enum_type = CatalystType(code)
            except ValueError:
                return 25.0
        return self._score_config.score_for(enum_type)

    def tradability_weight(self, catalyst_type: CatalystType | str) -> float | None:
        """Return DB tradability weight when taxonomy mode is enabled."""
        if not self._use_db_taxonomy or self._taxonomy_cache is None:
            return None
        code = catalyst_type.value if isinstance(catalyst_type, CatalystType) else str(catalyst_type)
        entry = self._taxonomy_cache.get_by_code(code)
        return float(entry.tradability_weight) if entry else None

    def is_weak_type(self, catalyst_type: CatalystType | str) -> bool:
        """Return whether catalyst is considered weak for direct-news cap."""
        if self._use_db_taxonomy and self._taxonomy_cache is not None:
            code = catalyst_type.value if isinstance(catalyst_type, CatalystType) else str(catalyst_type)
            entry = self._taxonomy_cache.get_by_code(code)
            if entry is not None:
                return entry.tradability_weight < WEAK_TRADABILITY_THRESHOLD
        enum_type = catalyst_type if isinstance(catalyst_type, CatalystType) else None
        if enum_type is None:
            try:
                enum_type = CatalystType(code)
            except ValueError:
                return False
        return enum_type in WEAK_CATALYST_TYPES

    def score_with_direct_news_cap(
        self,
        catalyst_type: CatalystType | str,
        *,
        direct_company_news: bool,
        direction: SentimentDirection | None = None,
        cap_without_direct: float = 15.0,
    ) -> float:
        """Score catalyst; cap weak types when news is not company-specific."""
        base = self.score(catalyst_type, direction=direction)
        if direct_company_news:
            return base
        if self.is_weak_type(catalyst_type):
            return min(base, cap_without_direct)
        return min(base, max(cap_without_direct, base * 0.5))
