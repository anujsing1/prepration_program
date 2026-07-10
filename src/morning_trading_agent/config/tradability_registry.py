"""Authoritative tradability score priors by catalyst type and category."""

from morning_trading_agent.domain.value_objects.catalyst import CatalystType
from morning_trading_agent.domain.value_objects.catalyst_tradability import CatalystTradabilityCategory


def default_tradability_by_type() -> dict[CatalystType, float]:
    return {
        CatalystType.ORDER_WIN: 95.0,
        CatalystType.LARGE_CONTRACT: 95.0,
        CatalystType.EARNINGS_BEAT: 90.0,
        CatalystType.BUYBACK: 88.0,
        CatalystType.REGULATORY_APPROVAL: 88.0,
        CatalystType.ACQUISITION: 85.0,
        CatalystType.PARTNERSHIP: 65.0,
        CatalystType.CAPEX_EXPANSION: 60.0,
        CatalystType.INVESTOR_MEETING: 10.0,
        CatalystType.ANALYST_MEETING: 10.0,
        CatalystType.PLANT_VISIT: 8.0,
        CatalystType.DIVIDEND_PROCEDURE: 12.0,
        CatalystType.BOARD_MEETING: 15.0,
        CatalystType.COMPLIANCE_FILING: 8.0,
        CatalystType.CORPORATE_COMMUNICATION: 12.0,
        CatalystType.GENERAL_UPDATE: 10.0,
        CatalystType.BROKER_RATING: 15.0,
        CatalystType.ANALYST_OPINION: 12.0,
        CatalystType.DEFENCE_PROCUREMENT: 90.0,
        CatalystType.GOVERNMENT_SPENDING: 85.0,
        CatalystType.STRATEGIC_PROCUREMENT: 82.0,
        CatalystType.THEMATIC_DEMAND_SURGE: 70.0,
        CatalystType.INDUSTRY_POLICY_CHANGE: 65.0,
        CatalystType.EXCHANGE_CLARIFICATION: 5.0,
    }


def default_tradability_by_category() -> dict[CatalystTradabilityCategory, float]:
    return {
        CatalystTradabilityCategory.EARNINGS_BEAT: 95.0,
        CatalystTradabilityCategory.ORDER_WIN: 92.0,
        CatalystTradabilityCategory.GOVT_CONTRACT: 90.0,
        CatalystTradabilityCategory.ACQUISITION: 90.0,
        CatalystTradabilityCategory.PROMOTER_BUYING: 88.0,
        CatalystTradabilityCategory.REGULATORY_APPROVAL: 88.0,
        CatalystTradabilityCategory.FUND_RAISE: 85.0,
        CatalystTradabilityCategory.CAPACITY_EXPANSION: 85.0,
        CatalystTradabilityCategory.MAJOR_PARTNERSHIP: 85.0,
        CatalystTradabilityCategory.BROKER_UPGRADE: 55.0,
        CatalystTradabilityCategory.PRODUCT_LAUNCH: 50.0,
        CatalystTradabilityCategory.MANAGEMENT_CHANGE: 45.0,
        CatalystTradabilityCategory.OTHER: 15.0,
        CatalystTradabilityCategory.GENERIC_MENTION: 5.0,
        CatalystTradabilityCategory.INVESTOR_PRESENTATION: 10.0,
        CatalystTradabilityCategory.INVESTOR_MEETING: 10.0,
        CatalystTradabilityCategory.POSTAL_BALLOT: 0.0,
        CatalystTradabilityCategory.VOTING_RESULT: 0.0,
        CatalystTradabilityCategory.SHAREHOLDER_NOTICE: 5.0,
        CatalystTradabilityCategory.AGM_NOTICE: 5.0,
        CatalystTradabilityCategory.EGM_NOTICE: 5.0,
        CatalystTradabilityCategory.MEETING_PROCEEDINGS: 5.0,
        CatalystTradabilityCategory.COMPLIANCE_FILING: 5.0,
        CatalystTradabilityCategory.NEWSPAPER_ADVERTISEMENT: 5.0,
        CatalystTradabilityCategory.EXCHANGE_INTIMATION: 5.0,
        CatalystTradabilityCategory.RECORD_DATE_NOTICE: 5.0,
        CatalystTradabilityCategory.CORPORATE_GOVERNANCE_FILING: 5.0,
        CatalystTradabilityCategory.ROUTINE_REGULATORY_DISCLOSURE: 5.0,
    }


TRADABILITY_SCORE_BY_TYPE: dict[CatalystType, float] = default_tradability_by_type()
TRADABILITY_SCORE_BY_CATEGORY: dict[CatalystTradabilityCategory, float] = (
    default_tradability_by_category()
)
