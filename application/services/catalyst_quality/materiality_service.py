"""Scores whether a catalyst is materially significant."""

from morning_trading_agent.config.premarket_config import MaterialityConfig, NonTradableCatalystConfig
from morning_trading_agent.domain.entities.article import SentimentAnalysis
from morning_trading_agent.domain.value_objects.catalyst import CatalystType
from morning_trading_agent.domain.value_objects.catalyst_quality import CatalystMagnitude


class MaterialityService:
    """Rule-based materiality scoring."""

    _HIGH_MATERIALITY_TYPES = frozenset(
        {
            CatalystType.ORDER_WIN,
            CatalystType.LARGE_CONTRACT,
            CatalystType.EARNINGS_BEAT,
            CatalystType.BUYBACK,
            CatalystType.ACQUISITION,
            CatalystType.REGULATORY_APPROVAL,
            CatalystType.PROJECT_COMMISSIONING,
            CatalystType.INSTITUTIONAL_BUYING,
            CatalystType.DEFENCE_PROCUREMENT,
            CatalystType.GOVERNMENT_SPENDING,
            CatalystType.STRATEGIC_PROCUREMENT,
        }
    )
    _LOW_MATERIALITY_TYPES = frozenset(
        {
            CatalystType.INVESTOR_MEETING,
            CatalystType.ANALYST_MEETING,
            CatalystType.PLANT_VISIT,
            CatalystType.DIVIDEND_PROCEDURE,
            CatalystType.COMPLIANCE_FILING,
            CatalystType.CORPORATE_COMMUNICATION,
            CatalystType.GENERAL_UPDATE,
            CatalystType.BOARD_MEETING,
        }
    )

    def __init__(
        self,
        *,
        config: MaterialityConfig | None = None,
        non_tradable_config: NonTradableCatalystConfig | None = None,
    ) -> None:
        self._config = config or MaterialityConfig()
        self._non_tradable = non_tradable_config or NonTradableCatalystConfig()

    def score(
        self,
        sentiment: SentimentAnalysis,
        *,
        magnitude: CatalystMagnitude,
        magnitude_score: float,
        financial_value_crore: float | None = None,
        strategic_importance: str | None = None,
    ) -> float:
        catalyst_type = sentiment.primary_catalyst_type
        if catalyst_type in self._non_tradable.non_tradable_types:
            return self._config.non_tradable_cap

        base = self._config.materiality_by_type.get(
            catalyst_type, self._type_base(catalyst_type)
        )
        blended = base + magnitude_score * self._config.magnitude_multiplier

        if financial_value_crore is not None:
            if financial_value_crore >= self._config.value_crore_high_threshold:
                blended += self._config.value_crore_high_bonus
            elif financial_value_crore < 5.0:
                blended = min(blended, 35.0)

        if strategic_importance:
            importance = strategic_importance.lower()
            if "transformational" in importance or "significant" in importance:
                blended += 15.0
            elif "routine" in importance:
                blended = min(blended, 30.0)

        if sentiment.thematic_sector_catalyst:
            blended = max(blended, 70.0)

        return round(max(0.0, min(100.0, blended)), 2)

    def _type_base(self, catalyst_type: CatalystType) -> float:
        if catalyst_type in self._HIGH_MATERIALITY_TYPES:
            return 85.0
        if catalyst_type in self._LOW_MATERIALITY_TYPES:
            return 15.0
        if catalyst_type in {CatalystType.PARTNERSHIP, CatalystType.CAPEX_EXPANSION}:
            return 55.0
        return self._config.default_materiality
