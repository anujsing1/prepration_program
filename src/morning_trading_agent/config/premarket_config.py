"""Pre-market configuration models."""

from typing import Literal

from pydantic import BaseModel, Field

from morning_trading_agent.domain.value_objects.catalyst import CatalystType
from morning_trading_agent.domain.value_objects.catalyst_tier import (
    DEFAULT_TIER_1_TYPES,
    DEFAULT_TIER_2_TYPES,
    DEFAULT_TIER_3_TYPES,
)
from morning_trading_agent.config.tradability_registry import (
    TRADABILITY_SCORE_BY_CATEGORY,
    TRADABILITY_SCORE_BY_TYPE,
    default_tradability_by_type,
)
from morning_trading_agent.domain.value_objects.catalyst_quality import (
    DEFAULT_NON_TRADABLE_TYPES,
    DEFAULT_STRONG_OVERRIDE_TYPES,
    CatalystMagnitude,
)

_default_tradability_by_type = default_tradability_by_type


def _default_catalyst_scores() -> dict[CatalystType, float]:
    return {
        CatalystType.ORDER_WIN: 100.0,
        CatalystType.MAJOR_ORDER_WIN: 98.0,
        CatalystType.DEFENCE_ORDER: 98.0,
        CatalystType.LARGE_CONTRACT: 95.0,
        CatalystType.FDA_APPROVAL: 90.0,
        CatalystType.PROMOTER_BUYING: 92.0,
        CatalystType.EARNINGS_BEAT: 95.0,
        CatalystType.EARNINGS: 95.0,
        CatalystType.EARNINGS_MISS: 15.0,
        CatalystType.REGULATORY_RISK: 12.0,
        CatalystType.BROKER_DOWNGRADE: 12.0,
        CatalystType.PROMOTER_SELLING: 10.0,
        CatalystType.SECTOR_HEADWIND: 15.0,
        CatalystType.BUYBACK: 90.0,
        CatalystType.ACQUISITION: 90.0,
        CatalystType.REGULATORY_APPROVAL: 90.0,
        CatalystType.PROJECT_COMMISSIONING: 85.0,
        CatalystType.INSTITUTIONAL_BUYING: 85.0,
        CatalystType.PARTNERSHIP: 80.0,
        CatalystType.FUND_RAISE: 80.0,
        CatalystType.MANAGEMENT_GUIDANCE: 80.0,
        CatalystType.CAPEX_EXPANSION: 75.0,
        CatalystType.CORPORATE_ACTION: 78.0,
        CatalystType.SECTOR_TAILWIND: 60.0,
        CatalystType.DEFENCE_PROCUREMENT: 95.0,
        CatalystType.GOVERNMENT_SPENDING: 90.0,
        CatalystType.STRATEGIC_PROCUREMENT: 88.0,
        CatalystType.THEMATIC_DEMAND_SURGE: 75.0,
        CatalystType.INDUSTRY_POLICY_CHANGE: 70.0,
        CatalystType.EXCHANGE_CLARIFICATION: 8.0,
        CatalystType.CLINICAL_TRIAL: 92.0,
        CatalystType.REGULATORY_MILESTONE: 90.0,
        CatalystType.JV_ANNOUNCEMENT: 82.0,
        CatalystType.MANUFACTURING_EXPANSION: 80.0,
        CatalystType.EXPORT_OPPORTUNITY: 65.0,
        CatalystType.POLICY_BENEFICIARY: 70.0,
        CatalystType.INVESTOR_MEETING: 12.0,
        CatalystType.ANALYST_MEETING: 10.0,
        CatalystType.PLANT_VISIT: 8.0,
        CatalystType.DIVIDEND_PROCEDURE: 12.0,
        CatalystType.COMPLIANCE_FILING: 8.0,
        CatalystType.CORPORATE_COMMUNICATION: 10.0,
        CatalystType.GENERAL_UPDATE: 5.0,
        CatalystType.BOARD_MEETING: 12.0,
        CatalystType.MANAGEMENT_CHANGE: 25.0,
        CatalystType.BROKER_RATING: 15.0,
        CatalystType.BROKER_UPGRADE: 15.0,
        CatalystType.DIVIDEND_COMMUNICATION: 20.0,
        CatalystType.ANALYST_OPINION: 10.0,
        CatalystType.TRADE_SPOTLIGHT: 10.0,
        CatalystType.STOCKS_TO_WATCH: 5.0,
        CatalystType.GENERIC_MENTION: 0.0,
        CatalystType.GENERIC_MARKET_NEWS: 0.0,
        CatalystType.OTHER: 25.0,
    }


class CatalystScoreConfig(BaseModel):
    """Configurable catalyst type scores."""

    scores: dict[CatalystType, float] = Field(default_factory=_default_catalyst_scores)

    def score_for(self, catalyst_type: CatalystType) -> float:
        return self.scores.get(catalyst_type, 25.0)


class RankingWeightConfig(BaseModel):
    """Configurable pre-market hybrid ranking weights."""

    catalyst: float = 0.40
    technical: float = 0.35
    sentiment: float = 0.10
    confidence: float = 0.05
    freshness: float = 0.05
    priority: float = 0.05

    def validate_weights(self) -> None:
        total = (
            self.catalyst
            + self.technical
            + self.sentiment
            + self.confidence
            + self.freshness
            + self.priority
        )
        if abs(total - 1.0) > 0.001:
            msg = f"Ranking weights must sum to 1.0, got {total}"
            raise ValueError(msg)


class CatalystRejectionConfig(BaseModel):
    """Configurable catalyst-based rejection thresholds."""

    min_catalyst_score: float = 20.0
    min_catalyst_score_without_direct_news: float = 40.0
    min_technical_score: float = 50.0
    reject_weak_catalyst_types: bool = True
    min_tradability_score: float | None = None
    min_materiality_score: float | None = None
    min_tradability_for_indirect_news: float = 60.0
    thematic_tradability_floor: float = 65.0
    thematic_materiality_floor: float = 60.0
    tier1_technical_override_min_catalyst: float = 80.0
    tier1_technical_override_min_technical: float = 35.0
    tier2_min_catalyst_score: float = 25.0
    tier2_min_technical_score: float = 55.0
    tier2_min_sentiment_score: float = 55.0
    reject_bearish_for_long_watchlist: bool = False
    reject_neutral_low_conviction: bool = False
    tier3_min_effective_catalyst: float = 40.0


class CatalystTierConfig(BaseModel):
    """Catalyst tier membership for filter policy."""

    tier_1_types: frozenset[CatalystType] = DEFAULT_TIER_1_TYPES
    tier_2_types: frozenset[CatalystType] = DEFAULT_TIER_2_TYPES
    tier_3_types: frozenset[CatalystType] = DEFAULT_TIER_3_TYPES
    tier_2_weak_types: frozenset[CatalystType] = frozenset(
        {
            CatalystType.BROKER_RATING,
            CatalystType.ANALYST_OPINION,
            CatalystType.TRADE_SPOTLIGHT,
            CatalystType.STOCKS_TO_WATCH,
        }
    )


class ImpactWeightConfig(BaseModel):
    """Weights for composite impact quality (normalized at runtime)."""

    revenue_impact: float = 0.15
    earnings_impact: float = 0.20
    balance_sheet_impact: float = 0.10
    valuation_impact: float = 0.10
    institutional_relevance: float = 0.15
    urgency: float = 0.10
    tradability: float = 0.20
    penny_stock_penalty: float = 15.0

    def normalized(self) -> dict[str, float]:
        items = {
            "revenue_impact": self.revenue_impact,
            "earnings_impact": self.earnings_impact,
            "balance_sheet_impact": self.balance_sheet_impact,
            "valuation_impact": self.valuation_impact,
            "institutional_relevance": self.institutional_relevance,
            "urgency": self.urgency,
            "tradability": self.tradability,
        }
        total = sum(items.values()) or 1.0
        return {name: weight / total for name, weight in items.items()}


class AdaptiveThresholdConfig(BaseModel):
    """Adaptive percentile thresholds derived from current candidate pool."""

    config_floor: float = 25.0
    p50_margin: float = 10.0
    technical_floor: float = 30.0
    technical_margin: float = 10.0
    fallback_composite_delta: float = 15.0
    fallback_technical_delta: float = 10.0


class AdaptiveWatchlistConfig(BaseModel):
    """Second-pass relaxed filter when survivors below minimum."""

    enabled: bool = True
    relaxed_technical_delta: float = 10.0
    relaxed_catalyst_delta: float = 5.0
    relaxed_min_tradability_indirect: float = 50.0
    allow_tier2_broker_in_relaxed: bool = True


class ProgressiveRelaxationConfig(BaseModel):
    """Institutional progressive watchlist relaxation passes."""

    freshness_pass1_delta: float = 5.0
    freshness_pass2_total_delta: float = 15.0
    technical_rescue_min: float = 60.0


class FilterRelaxationOverlay(BaseModel):
    """Per-pass filter overlay applied to relaxable rejects."""

    pass_name: str
    min_freshness_override: float | None = None
    allow_secondary_catalysts: bool = False
    technical_rescue_min: float | None = None


class RankingWeightV2Config(BaseModel):
    """Ranking Formula V2 weights (must sum to 1.0)."""

    catalyst: float = 0.30
    magnitude: float = 0.20
    materiality: float = 0.15
    tradability: float = 0.10
    technical: float = 0.15
    sentiment: float = 0.05
    confidence: float = 0.05

    def validate_weights(self) -> None:
        total = (
            self.catalyst
            + self.magnitude
            + self.materiality
            + self.tradability
            + self.technical
            + self.sentiment
            + self.confidence
        )
        if abs(total - 1.0) > 0.001:
            msg = f"Ranking V2 weights must sum to 1.0, got {total}"
            raise ValueError(msg)


def _default_magnitude_scores() -> dict[CatalystMagnitude, float]:
    return {
        CatalystMagnitude.VERY_HIGH: 100.0,
        CatalystMagnitude.HIGH: 80.0,
        CatalystMagnitude.MEDIUM: 50.0,
        CatalystMagnitude.LOW: 25.0,
        CatalystMagnitude.VERY_LOW: 5.0,
    }


def _default_type_baseline_magnitude() -> dict[CatalystType, CatalystMagnitude]:
    return {
        CatalystType.ORDER_WIN: CatalystMagnitude.VERY_HIGH,
        CatalystType.LARGE_CONTRACT: CatalystMagnitude.VERY_HIGH,
        CatalystType.EARNINGS_BEAT: CatalystMagnitude.HIGH,
        CatalystType.EARNINGS: CatalystMagnitude.HIGH,
        CatalystType.BUYBACK: CatalystMagnitude.HIGH,
        CatalystType.ACQUISITION: CatalystMagnitude.HIGH,
        CatalystType.REGULATORY_APPROVAL: CatalystMagnitude.HIGH,
        CatalystType.DEFENCE_PROCUREMENT: CatalystMagnitude.VERY_HIGH,
        CatalystType.GOVERNMENT_SPENDING: CatalystMagnitude.VERY_HIGH,
        CatalystType.STRATEGIC_PROCUREMENT: CatalystMagnitude.HIGH,
        CatalystType.THEMATIC_DEMAND_SURGE: CatalystMagnitude.HIGH,
        CatalystType.INDUSTRY_POLICY_CHANGE: CatalystMagnitude.MEDIUM,
        CatalystType.EXCHANGE_CLARIFICATION: CatalystMagnitude.VERY_LOW,
        CatalystType.INVESTOR_MEETING: CatalystMagnitude.VERY_LOW,
        CatalystType.ANALYST_MEETING: CatalystMagnitude.VERY_LOW,
        CatalystType.PLANT_VISIT: CatalystMagnitude.VERY_LOW,
        CatalystType.BOARD_MEETING: CatalystMagnitude.VERY_LOW,
        CatalystType.DIVIDEND_PROCEDURE: CatalystMagnitude.VERY_LOW,
        CatalystType.DIVIDEND_COMMUNICATION: CatalystMagnitude.VERY_LOW,
        CatalystType.COMPLIANCE_FILING: CatalystMagnitude.VERY_LOW,
        CatalystType.CORPORATE_COMMUNICATION: CatalystMagnitude.VERY_LOW,
        CatalystType.GENERAL_UPDATE: CatalystMagnitude.VERY_LOW,
        CatalystType.BROKER_RATING: CatalystMagnitude.VERY_LOW,
        CatalystType.ANALYST_OPINION: CatalystMagnitude.VERY_LOW,
    }


class CatalystMagnitudeConfig(BaseModel):
    """Catalyst magnitude scoring configuration."""

    magnitude_score_by_level: dict[CatalystMagnitude, float] = Field(
        default_factory=_default_magnitude_scores
    )
    value_crore_thresholds: list[tuple[float, CatalystMagnitude]] = Field(
        default_factory=lambda: [
            (500.0, CatalystMagnitude.VERY_HIGH),
            (100.0, CatalystMagnitude.HIGH),
            (25.0, CatalystMagnitude.MEDIUM),
            (5.0, CatalystMagnitude.LOW),
            (0.0, CatalystMagnitude.VERY_LOW),
        ]
    )
    type_baseline_magnitude: dict[CatalystType, CatalystMagnitude] = Field(
        default_factory=_default_type_baseline_magnitude
    )
    max_value_crore_sanity: float = 100_000.0

    def magnitude_for_value_crore(self, value_crore: float) -> CatalystMagnitude:
        for threshold, magnitude in self.value_crore_thresholds:
            if value_crore >= threshold:
                return magnitude
        return CatalystMagnitude.VERY_LOW

    def score_for_magnitude(self, magnitude: CatalystMagnitude) -> float:
        return self.magnitude_score_by_level.get(magnitude, 50.0)


class NonTradableCatalystConfig(BaseModel):
    """Non-tradable catalyst handling."""

    non_tradable_types: frozenset[CatalystType] = DEFAULT_NON_TRADABLE_TYPES
    mode: Literal["reject", "penalize"] = "reject"
    penalized_tradability_score: float = 5.0
    penalized_materiality_score: float = 10.0


class BrokerRatingConfig(BaseModel):
    """Broker-only catalyst score cap."""

    broker_only_catalyst_score: float = 10.0
    strong_override_types: frozenset[CatalystType] = DEFAULT_STRONG_OVERRIDE_TYPES
    strong_override_keywords: tuple[str, ...] = (
        "order win",
        "contract",
        "earnings beat",
        "buyback",
        "acquisition",
        "regulatory approval",
        "defence",
        "defense procurement",
    )


class TradabilityConfig(BaseModel):
    """Tradability score configuration."""

    tradability_by_type: dict[CatalystType, float] = Field(
        default_factory=_default_tradability_by_type
    )
    default_tradability: float = 45.0
    non_tradable_cap: float = 10.0
    materiality_weight: float = 0.35
    magnitude_weight: float = 0.25


class MaterialityConfig(BaseModel):
    """Materiality score configuration."""

    materiality_by_type: dict[CatalystType, float] = Field(default_factory=dict)
    default_materiality: float = 50.0
    non_tradable_cap: float = 15.0
    magnitude_multiplier: float = 0.40
    value_crore_high_threshold: float = 100.0
    value_crore_high_bonus: float = 25.0


class TechnicalWeightConfig(BaseModel):
    """Configurable technical score component weights."""

    trend_strength: float = 0.22
    support_resistance: float = 0.12
    breakout_readiness: float = 0.18
    breakout_20d: float = 0.10
    relative_volume: float = 0.18
    momentum: float = 0.12
    atr_volatility: float = 0.08

    def validate_weights(self) -> None:
        total = (
            self.trend_strength
            + self.support_resistance
            + self.breakout_readiness
            + self.breakout_20d
            + self.relative_volume
            + self.momentum
            + self.atr_volatility
        )
        if abs(total - 1.0) > 0.001:
            msg = f"Technical weights must sum to 1.0, got {total}"
            raise ValueError(msg)


class SectorMomentumConfig(BaseModel):
    """Sector momentum scoring thresholds."""

    strong_momentum_threshold: float = 2.0
    weak_momentum_threshold: float = -1.0
    strong_sector_bonus: float = 12.0
    neutral_sector_bonus: float = 5.0
    relative_volume_breakout_threshold: float = 2.0
    breakout_20d_bonus: float = 15.0


class FreshnessThresholdConfig(BaseModel):
    """Session-band and legacy age-tier freshness scores."""

    session_band_scores: dict[str, float] = Field(
        default_factory=lambda: {
            "AFTER_MARKET": 100.0,
            "OVERNIGHT": 92.0,
            "PREMARKET": 88.0,
            "INTRADAY": 55.0,
            "STALE": 10.0,
        }
    )
    tiers: list[tuple[int, float]] = Field(
        default_factory=lambda: [
            (60, 100.0),
            (180, 90.0),
            (360, 80.0),
            (720, 60.0),
            (1440, 40.0),
        ]
    )
    stale_score: float = 10.0

    def score_for_band(self, band: str) -> float:
        return self.session_band_scores.get(band, self.stale_score)

    def score_for_age(self, age_minutes: int) -> float:
        for max_minutes, score in self.tiers:
            if age_minutes < max_minutes:
                return score
        return self.stale_score


class CatalystEscalationConfig(BaseModel):
    """Rules for escalating thematic government/defence catalysts."""

    government_procurement_crore_threshold: float = 1000.0
    defence_keywords: tuple[str, ...] = (
        "defence",
        "defense",
        "drone",
        "procurement",
        "defence order",
        "defense order",
        "armed forces",
        "military",
        "mod approval",
        "ministry of defence",
    )
    government_keywords: tuple[str, ...] = (
        "government spending",
        "government procurement",
        "capex program",
        "national program",
        "crore program",
        "crore scheme",
        "budget allocation",
    )
    sector_keywords: tuple[str, ...] = ("drone", "defence", "defense", "aerospace")
    escalatable_types: frozenset[CatalystType] = frozenset(
        {
            CatalystType.SECTOR_TAILWIND,
            CatalystType.GENERAL_UPDATE,
            CatalystType.OTHER,
            CatalystType.INDUSTRY_POLICY_CHANGE,
            CatalystType.THEMATIC_DEMAND_SURGE,
        }
    )


class NearMissConfig(BaseModel):
    """Thresholds for near-miss candidate review."""

    min_score: float = 60.0
    min_catalyst_score: float = 60.0
    min_tradability_score: float = 60.0
    min_materiality_score: float = 60.0


def _default_news_quality_by_type() -> dict[CatalystType, float]:
    return {
        CatalystType.ORDER_WIN: 100.0,
        CatalystType.LARGE_CONTRACT: 95.0,
        CatalystType.EARNINGS_BEAT: 95.0,
        CatalystType.EARNINGS: 90.0,
        CatalystType.BUYBACK: 90.0,
        CatalystType.ACQUISITION: 90.0,
        CatalystType.REGULATORY_APPROVAL: 88.0,
        CatalystType.DEFENCE_PROCUREMENT: 95.0,
        CatalystType.CLINICAL_TRIAL: 90.0,
        CatalystType.REGULATORY_MILESTONE: 88.0,
        CatalystType.JV_ANNOUNCEMENT: 80.0,
        CatalystType.MANUFACTURING_EXPANSION: 78.0,
        CatalystType.EXPORT_OPPORTUNITY: 72.0,
        CatalystType.POLICY_BENEFICIARY: 68.0,
        CatalystType.GOVERNMENT_SPENDING: 92.0,
        CatalystType.STRATEGIC_PROCUREMENT: 88.0,
        CatalystType.PROJECT_COMMISSIONING: 85.0,
        CatalystType.PARTNERSHIP: 75.0,
        CatalystType.SECTOR_TAILWIND: 55.0,
        CatalystType.THEMATIC_DEMAND_SURGE: 70.0,
        CatalystType.INDUSTRY_POLICY_CHANGE: 65.0,
        CatalystType.BROKER_RATING: 25.0,
        CatalystType.BROKER_UPGRADE: 25.0,
        CatalystType.GENERAL_UPDATE: 0.0,
        CatalystType.OTHER: 15.0,
        CatalystType.GENERIC_MENTION: 0.0,
        CatalystType.GENERIC_MARKET_NEWS: 0.0,
        CatalystType.TRADE_SPOTLIGHT: 10.0,
        CatalystType.STOCKS_TO_WATCH: 5.0,
        CatalystType.EXCHANGE_CLARIFICATION: 5.0,
    }


class NewsQualityConfig(BaseModel):
    """Article quality scoring before stock extraction."""

    quality_by_type: dict[CatalystType, float] = Field(
        default_factory=_default_news_quality_by_type
    )
    min_article_quality: float = 15.0
    default_quality: float = 30.0


class WatchlistQualityConfig(BaseModel):
    """Configurable watchlist quality filter thresholds."""

    min_price_inr: float = 20.0
    min_average_volume: float = 100_000.0
    min_turnover_20d_inr: float = 100_000_000.0
    min_sentiment_score: float = 40.0
    min_technical_score: float = 45.0
    min_relative_volume: float = 0.3
    use_turnover_primary: bool = True
    reject_duplicate_catalysts: bool = False
    max_symbols_per_event: int = 4
    min_event_beneficiary_weight: float = 0.35


class IngressScoringConfig(BaseModel):
    """Weights for NQS / CRS / TRS composite."""

    weight_nqs: float = 0.40
    weight_crs: float = 0.35
    weight_trs: float = 0.25


class EventClusterConfig(BaseModel):
    """Event-level clustering parameters."""

    min_beneficiary_weight: float = 0.35
    max_beneficiaries_per_event: int = 4


class BeneficiaryExtractionConfig(BaseModel):
    """Beneficiary extraction thresholds."""

    max_symbols_per_article: int = 6
    llm_crs_threshold: float = 70.0


class HybridCatalystConfig(BaseModel):
    """Hybrid catalyst classifier settings."""

    rule_confidence_skip_llm: float = 0.85


class IngressFilterConfig(BaseModel):
    """Pre-LLM article ingress gate."""

    enabled: bool = True
    min_ingress_score: float = 55.0
    scoring: IngressScoringConfig = Field(default_factory=IngressScoringConfig)
    event_cluster: EventClusterConfig = Field(default_factory=EventClusterConfig)


class RankingWeightV3Config(BaseModel):
    """Institutional ranking V3 weights (must sum to 1.0)."""

    event: float = 0.40
    technical: float = 0.30
    liquidity: float = 0.20
    sentiment: float = 0.05
    freshness: float = 0.05

    def validate_weights(self) -> None:
        total = self.event + self.technical + self.liquidity + self.sentiment + self.freshness
        if abs(total - 1.0) > 0.001:
            msg = f"Ranking V3 weights must sum to 1.0, got {total}"
            raise ValueError(msg)


def swing_ranking_weight_v3() -> "RankingWeightV3Config":
    """Swing-default V3 composite weights."""
    return RankingWeightV3Config(
        event=0.35,
        technical=0.25,
        liquidity=0.20,
        sentiment=0.10,
        freshness=0.10,
    )


class TieredWatchlistConfig(BaseModel):
    """Score floors for tiered watchlist fill (T1 → T2 → T3)."""

    tier1_min_adjusted_score: float = 75.0
    tier2_min_adjusted_score: float = 60.0
    tier3_min_adjusted_score: float = 45.0


class PenaltyFrameworkConfig(BaseModel):
    """Soft penalty multipliers (swing profile)."""

    bearish_long_penalty: float = 0.85
    neutral_penalty: float = 0.92
    indirect_catalyst_penalty: float = 0.75
    weak_tier2_penalty: float = 0.85
    weak_technical_mid_penalty: float = 0.90
    weak_technical_low_penalty: float = 0.88
    weak_sentiment_penalty: float = 0.92
    liquidity_soft_penalty: float = 0.90
    duplicate_catalyst_penalty: float = 0.95
    tier3_mid_catalyst_penalty: float = 0.80


class TradingProfileConfig(BaseModel):
    """Liquidity, filter, and gate behavior by trading profile."""

    profile: Literal["institutional", "swing", "retail"] = "swing"
    use_penalty_framework: bool = True
    gate_rejects_non_trade: bool = False
    reject_bearish_for_long_watchlist: bool = False
    min_turnover_20d_inr: float = 30_000_000.0
    min_inst_tradability: float = 35.0
    liquidity_hard_reject_below: float = 20.0
    min_tradability_for_indirect_news: float = 45.0
    tier3_hard_reject_below: float = 15.0
    min_catalyst_hard_reject: float = 10.0
    tiered: TieredWatchlistConfig = Field(default_factory=TieredWatchlistConfig)
    penalties: PenaltyFrameworkConfig = Field(default_factory=PenaltyFrameworkConfig)

    @classmethod
    def for_profile(cls, profile: Literal["institutional", "swing", "retail"]) -> "TradingProfileConfig":
        presets: dict[str, dict[str, object]] = {
            "institutional": {
                "use_penalty_framework": False,
                "gate_rejects_non_trade": True,
                "reject_bearish_for_long_watchlist": True,
                "min_turnover_20d_inr": 100_000_000.0,
                "min_inst_tradability": 50.0,
                "liquidity_hard_reject_below": 25.0,
                "min_tradability_for_indirect_news": 60.0,
            },
            "swing": {
                "use_penalty_framework": True,
                "gate_rejects_non_trade": False,
                "reject_bearish_for_long_watchlist": False,
                "min_turnover_20d_inr": 30_000_000.0,
                "min_inst_tradability": 35.0,
                "liquidity_hard_reject_below": 20.0,
                "min_tradability_for_indirect_news": 45.0,
            },
            "retail": {
                "use_penalty_framework": True,
                "gate_rejects_non_trade": False,
                "reject_bearish_for_long_watchlist": False,
                "min_turnover_20d_inr": 10_000_000.0,
                "min_inst_tradability": 25.0,
                "liquidity_hard_reject_below": 15.0,
                "min_tradability_for_indirect_news": 35.0,
                "tiered": TieredWatchlistConfig(
                    tier1_min_adjusted_score=70.0,
                    tier2_min_adjusted_score=55.0,
                    tier3_min_adjusted_score=40.0,
                ),
            },
        }
        data = presets.get(profile, presets["swing"])
        return cls(profile=profile, **data)


class ProfessionalTraderGateConfig(BaseModel):
    """Watchlist professional trader validation thresholds."""

    min_technical_score: float = 40.0
    min_catalyst_strength: float = 50.0
    min_final_score: float = 45.0
    min_expected_impact: float = 55.0
    min_tradeability: float = 50.0
    min_freshness: float = 70.0
    accept_watch_tag: bool = False
    label_only: bool = False


class TechnicalCompositeConfig(BaseModel):
    """Pillar weights for institutional technical composite."""

    trend: float = 0.25
    momentum: float = 0.25
    volume: float = 0.25
    structure: float = 0.25
    accumulation_bonus_max: float = 10.0


class TradabilityScoreConfig(BaseModel):
    """Institutional tradability continuous score."""

    min_tradability_hard_floor: float = 25.0
    weight_traded_value: float = 0.30
    weight_market_cap: float = 0.25
    weight_relative_volume: float = 0.15
    weight_slippage: float = 0.15
    weight_spread: float = 0.15
    min_market_cap_inr: float = 500_000_000.0
