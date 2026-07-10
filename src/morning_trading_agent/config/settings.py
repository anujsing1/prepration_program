"""Application configuration via Pydantic Settings."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from morning_trading_agent.domain.value_objects.catalyst_quality import CatalystMagnitude

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from morning_trading_agent.config.premarket_config import (
    AdaptiveThresholdConfig,
    AdaptiveWatchlistConfig,
    BeneficiaryExtractionConfig,
    BrokerRatingConfig,
    CatalystEscalationConfig,
    CatalystMagnitudeConfig,
    CatalystRejectionConfig,
    CatalystScoreConfig,
    FreshnessThresholdConfig,
    ImpactWeightConfig,
    IngressFilterConfig,
    MaterialityConfig,
    NearMissConfig,
    NewsQualityConfig,
    NonTradableCatalystConfig,
    ProfessionalTraderGateConfig,
    RankingWeightConfig,
    RankingWeightV2Config,
    RankingWeightV3Config,
    TradingProfileConfig,
    swing_ranking_weight_v3,
    SectorMomentumConfig,
    TechnicalWeightConfig,
    TradabilityConfig,
    TradabilityScoreConfig,
    WatchlistQualityConfig,
)
from morning_trading_agent.domain.value_objects.trading_session import TradingSessionMode

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_ENV_FILE = _PROJECT_ROOT / ".env"

_NESTED_SETTINGS_CONFIG = SettingsConfigDict(
    env_file=str(_ENV_FILE),
    env_file_encoding="utf-8",
    extra="ignore",
)


class DatabaseSettings(BaseSettings):
    """PostgreSQL connection settings."""

    model_config = _NESTED_SETTINGS_CONFIG

    database_url: str = Field(
        default="postgresql+asyncpg://mta:mta@localhost:5432/morning_trading_agent",
        alias="DATABASE_URL",
    )


class TelegramSettings(BaseSettings):
    """Telegram bot settings."""

    model_config = _NESTED_SETTINGS_CONFIG

    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str = Field(default="", alias="TELEGRAM_CHAT_ID")


class OllamaSettings(BaseSettings):
    """Ollama OpenAI-compatible LLM settings."""

    model_config = _NESTED_SETTINGS_CONFIG

    ollama_base_url: str = Field(
        default="http://localhost:11434/v1",
        alias="OLLAMA_BASE_URL",
    )
    ollama_model: str = Field(default="qwen2.5:7b", alias="OLLAMA_MODEL")
    ollama_timeout_seconds: float = Field(default=30.0, alias="OLLAMA_TIMEOUT_SECONDS")
    ollama_max_retries: int = Field(default=1, alias="OLLAMA_MAX_RETRIES")
    ollama_batch_enabled: bool = Field(default=False, alias="OLLAMA_BATCH_ENABLED")


class RagSettings(BaseSettings):
    """Catalyst RAG retrieval settings."""

    model_config = _NESTED_SETTINGS_CONFIG

    embedding_model: str = Field(
        default="nomic-embed-text",
        alias="RAG_EMBEDDING_MODEL",
        description="Ollama embedding model (pull with: ollama pull nomic-embed-text)",
    )
    top_k: int = Field(default=5, alias="RAG_TOP_K")
    embedding_cache_path: str = Field(
        default=str(_PROJECT_ROOT / ".artifacts" / "rag" / "embedding_cache.json"),
        alias="RAG_EMBEDDING_CACHE_PATH",
    )


class MarketMemorySettings(BaseSettings):
    """Long-term market memory for research desk RAG."""

    model_config = _NESTED_SETTINGS_CONFIG

    root_path: str = Field(
        default=str(_PROJECT_ROOT / "market_memory"),
        alias="MARKET_MEMORY_PATH",
    )
    top_k: int = Field(default=5, alias="MARKET_MEMORY_TOP_K")
    enabled: bool = Field(default=True, alias="ENABLE_RESEARCH_DESK")


class GeminiSettings(BaseSettings):
    """Gemini LLM settings."""

    model_config = _NESTED_SETTINGS_CONFIG

    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    gemini_flash_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_FLASH_MODEL")
    gemini_pro_model: str = Field(default="gemini-2.5-pro", alias="GEMINI_PRO_MODEL")
    gemini_report_model: str = Field(
        default="gemini-2.5-flash",
        alias="GEMINI_REPORT_MODEL",
        description="Watchlist report model. Flash works on free tier; Pro requires billing.",
    )


class ApplicationSettings(BaseSettings):
    """Application runtime settings."""

    model_config = _NESTED_SETTINGS_CONFIG

    ranking_strategy: Literal[
        "premarket_hybrid",
        "premarket_hybrid_v2",
        "premarket_institutional_v3",
        "premarket_institutional_v4",
        "intraday_momentum_v1",
        "postmarket_review_v1",
        "hybrid",
        "news",
        "momentum",
    ] = Field(default="premarket_institutional_v3", alias="RANKING_STRATEGY")
    trading_session_mode: TradingSessionMode = Field(
        default=TradingSessionMode.AUTO, alias="TRADING_SESSION_MODE"
    )
    trading_session_override: str = Field(default="", alias="TRADING_SESSION_OVERRIDE")
    force_session: str = Field(default="", alias="FORCE_SESSION")
    premarket_strategy: str = Field(
        default="premarket_institutional_v3", alias="PREMARKET_STRATEGY"
    )
    intraday_strategy: str = Field(default="intraday_momentum_v1", alias="INTRADAY_STRATEGY")
    postmarket_strategy: str = Field(default="postmarket_review_v1", alias="POSTMARKET_STRATEGY")
    market_open_time: str = Field(default="09:15", alias="MARKET_OPEN_TIME")
    market_close_time: str = Field(default="15:30", alias="MARKET_CLOSE_TIME")
    after_market_end_time: str = Field(default="20:00", alias="AFTER_MARKET_END_TIME")
    run_datetime_override: str = Field(default="", alias="RUN_DATETIME_OVERRIDE")
    news_providers: str = Field(
        default="moneycontrol,economic_times,google_news,nse_announcements",
        alias="NEWS_PROVIDERS",
    )
    news_fetch_limit: int = Field(default=50, alias="NEWS_FETCH_LIMIT")
    news_lookback_hours: int = Field(default=24, alias="NEWS_LOOKBACK_HOURS")
    news_freshness_hours: float = Field(default=12.0, alias="NEWS_FRESHNESS_HOURS")
    use_session_freshness: bool = Field(default=True, alias="USE_SESSION_FRESHNESS")
    nse_holidays_path: str = Field(
        default=str(_PROJECT_ROOT / "config" / "nse_holidays.yaml"),
        alias="NSE_HOLIDAYS_PATH",
    )
    market_timezone: str = Field(default="Asia/Kolkata", alias="MARKET_TIMEZONE")
    session_fetch_buffer_minutes: int = Field(
        default=60, alias="SESSION_FETCH_BUFFER_MINUTES"
    )
    future_date_tolerance_minutes: int = Field(
        default=10, alias="FUTURE_DATE_TOLERANCE_MINUTES"
    )
    top_n_candidates: int = Field(default=10, alias="TOP_N_CANDIDATES")
    technical_lookback_days: int = Field(default=60, alias="TECHNICAL_LOOKBACK_DAYS")
    market_data_source: Literal["bhavcopy", "yfinance", "hybrid"] = Field(
        default="bhavcopy",
        alias="MARKET_DATA_SOURCE",
    )
    enable_telegram: bool = Field(default=False, alias="ENABLE_TELEGRAM")
    enable_database: bool = Field(default=False, alias="ENABLE_DATABASE")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    dry_run: bool = Field(default=False, alias="DRY_RUN")
    min_watchlist_size: int = Field(default=5, alias="MIN_WATCHLIST_SIZE")
    max_watchlist_size: int = Field(default=10, alias="MAX_WATCHLIST_SIZE")
    pro_gate_min_technical_score: float = Field(
        default=40.0, alias="PRO_GATE_MIN_TECHNICAL_SCORE"
    )
    pro_gate_min_catalyst_score: float = Field(
        default=50.0, alias="PRO_GATE_MIN_CATALYST_SCORE"
    )
    pro_gate_min_final_score: float = Field(default=45.0, alias="PRO_GATE_MIN_FINAL_SCORE")
    pro_gate_min_tradeability_score: float = Field(
        default=50.0, alias="PRO_GATE_MIN_TRADEABILITY_SCORE"
    )
    pro_gate_min_freshness_score: float = Field(
        default=70.0, alias="PRO_GATE_MIN_FRESHNESS_SCORE"
    )
    pro_gate_min_impact_score: float = Field(default=55.0, alias="PRO_GATE_MIN_IMPACT_SCORE")
    watchlist_relaxation_step: float = Field(default=5.0, alias="WATCHLIST_RELAXATION_STEP")
    watchlist_allow_relaxation: bool = Field(default=True, alias="WATCHLIST_ALLOW_RELAXATION")
    min_price_inr: float = Field(default=20.0, alias="MIN_PRICE_INR")
    min_average_volume: float = Field(default=100_000.0, alias="MIN_AVERAGE_VOLUME")
    min_sentiment_score: float = Field(default=40.0, alias="MIN_SENTIMENT_SCORE")
    min_technical_score: float = Field(default=45.0, alias="MIN_TECHNICAL_SCORE")
    min_catalyst_score: float = Field(default=20.0, alias="MIN_CATALYST_SCORE")
    min_catalyst_score_no_direct_news: float = Field(
        default=40.0, alias="MIN_CATALYST_SCORE_NO_DIRECT_NEWS"
    )
    min_technical_score_filter: float = Field(default=50.0, alias="MIN_TECHNICAL_SCORE_FILTER")
    ranking_weight_catalyst: float = Field(default=0.40, alias="RANKING_WEIGHT_CATALYST")
    ranking_weight_technical: float = Field(default=0.35, alias="RANKING_WEIGHT_TECHNICAL")
    ranking_weight_sentiment: float = Field(default=0.10, alias="RANKING_WEIGHT_SENTIMENT")
    ranking_weight_confidence: float = Field(default=0.05, alias="RANKING_WEIGHT_CONFIDENCE")
    ranking_weight_freshness: float = Field(default=0.05, alias="RANKING_WEIGHT_FRESHNESS")
    ranking_weight_priority: float = Field(default=0.05, alias="RANKING_WEIGHT_PRIORITY")
    ranking_v2_weight_catalyst: float = Field(default=0.30, alias="RANKING_V2_WEIGHT_CATALYST")
    ranking_v2_weight_magnitude: float = Field(default=0.20, alias="RANKING_V2_WEIGHT_MAGNITUDE")
    ranking_v2_weight_materiality: float = Field(
        default=0.15, alias="RANKING_V2_WEIGHT_MATERIALITY"
    )
    ranking_v2_weight_tradability: float = Field(
        default=0.10, alias="RANKING_V2_WEIGHT_TRADABILITY"
    )
    ranking_v2_weight_technical: float = Field(default=0.15, alias="RANKING_V2_WEIGHT_TECHNICAL")
    ranking_v2_weight_sentiment: float = Field(default=0.05, alias="RANKING_V2_WEIGHT_SENTIMENT")
    ranking_v2_weight_confidence: float = Field(
        default=0.05, alias="RANKING_V2_WEIGHT_CONFIDENCE"
    )
    broker_rating_score: float = Field(default=10.0, alias="BROKER_RATING_SCORE")
    non_tradable_catalyst_mode: Literal["reject", "penalize"] = Field(
        default="reject", alias="NON_TRADABLE_CATALYST_MODE"
    )
    min_tradability_score: float | None = Field(default=None, alias="MIN_TRADABILITY_SCORE")
    min_materiality_score: float | None = Field(default=None, alias="MIN_MATERIALITY_SCORE")
    magnitude_value_crore_very_high: float = Field(
        default=500.0, alias="MAGNITUDE_VALUE_CRORE_VERY_HIGH"
    )
    magnitude_value_crore_high: float = Field(default=100.0, alias="MAGNITUDE_VALUE_CRORE_HIGH")
    magnitude_value_crore_medium: float = Field(default=25.0, alias="MAGNITUDE_VALUE_CRORE_MEDIUM")
    magnitude_value_crore_low: float = Field(default=5.0, alias="MAGNITUDE_VALUE_CRORE_LOW")
    persist_all_filtered_candidates: bool = Field(
        default=False, alias="PERSIST_ALL_FILTERED_CANDIDATES"
    )
    min_article_quality_score: float = Field(default=15.0, alias="MIN_ARTICLE_QUALITY_SCORE")
    min_tradability_for_indirect_news: float = Field(
        default=60.0, alias="MIN_TRADABILITY_FOR_INDIRECT_NEWS"
    )
    thematic_tradability_floor: float = Field(default=65.0, alias="THEMATIC_TRADABILITY_FLOOR")
    thematic_materiality_floor: float = Field(default=60.0, alias="THEMATIC_MATERIALITY_FLOOR")
    government_procurement_crore_threshold: float = Field(
        default=1000.0, alias="GOVERNMENT_PROCUREMENT_CRORE_THRESHOLD"
    )
    near_miss_min_score: float = Field(default=60.0, alias="NEAR_MISS_MIN_SCORE")
    adaptive_watchlist_enabled: bool = Field(default=True, alias="ADAPTIVE_WATCHLIST_ENABLED")
    relaxed_technical_delta: float = Field(default=10.0, alias="RELAXED_TECHNICAL_DELTA")
    relaxed_catalyst_delta: float = Field(default=5.0, alias="RELAXED_CATALYST_DELTA")
    relaxed_min_tradability_indirect: float = Field(
        default=50.0, alias="RELAXED_MIN_TRADABILITY_INDIRECT"
    )
    min_turnover_20d_inr: float = Field(default=100_000_000.0, alias="MIN_TURNOVER_20D_INR")
    use_turnover_primary: bool = Field(default=True, alias="USE_TURNOVER_PRIMARY")
    tier1_technical_override_min_catalyst: float = Field(
        default=80.0, alias="TIER1_TECHNICAL_OVERRIDE_MIN_CATALYST"
    )
    tier1_technical_override_min_technical: float = Field(
        default=35.0, alias="TIER1_TECHNICAL_OVERRIDE_MIN_TECHNICAL"
    )
    ingress_filter_enabled: bool = Field(default=True, alias="INGRESS_FILTER_ENABLED")
    min_ingress_score: float = Field(default=55.0, alias="MIN_INGRESS_SCORE")
    beneficiary_extraction_enabled: bool = Field(
        default=True, alias="BENEFICIARY_EXTRACTION_ENABLED"
    )
    llm_provider: Literal["gemini", "ollama", "stub"] = Field(
        default="gemini",
        alias="LLM_PROVIDER",
    )
    llm_cache_enabled: bool = Field(default=True, alias="LLM_CACHE_ENABLED")
    template_report_first: bool = Field(default=True, alias="TEMPLATE_REPORT_FIRST")
    ranking_v3_weight_event: float = Field(default=0.40, alias="RANKING_V3_WEIGHT_EVENT")
    ranking_v3_weight_technical: float = Field(default=0.30, alias="RANKING_V3_WEIGHT_TECHNICAL")
    ranking_v3_weight_liquidity: float = Field(default=0.20, alias="RANKING_V3_WEIGHT_LIQUIDITY")
    ranking_v3_weight_sentiment: float = Field(default=0.05, alias="RANKING_V3_WEIGHT_SENTIMENT")
    ranking_v3_weight_freshness: float = Field(default=0.05, alias="RANKING_V3_WEIGHT_FRESHNESS")
    trading_profile: Literal["institutional", "swing", "retail"] = Field(
        default="swing", alias="TRADING_PROFILE"
    )


class Settings(BaseSettings):
    """Root settings aggregating all configuration groups."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    telegram: TelegramSettings = Field(default_factory=TelegramSettings)
    gemini: GeminiSettings = Field(default_factory=GeminiSettings)
    ollama: OllamaSettings = Field(default_factory=OllamaSettings)
    rag: RagSettings = Field(default_factory=RagSettings)
    market_memory: MarketMemorySettings = Field(default_factory=MarketMemorySettings)
    app: ApplicationSettings = Field(default_factory=ApplicationSettings)

    @property
    def news_provider_list(self) -> list[str]:
        """Parse comma-separated news provider names."""
        return [p.strip() for p in self.app.news_providers.split(",") if p.strip()]

    @property
    def telegram_enabled(self) -> bool:
        """True when Telegram notifications are requested and configured."""
        if not self.app.enable_telegram:
            return False
        return bool(
            self.telegram.telegram_bot_token.strip() and self.telegram.telegram_chat_id.strip()
        )

    @property
    def database_enabled(self) -> bool:
        """True when PostgreSQL persistence is requested."""
        return self.app.enable_database

    @property
    def resolved_runtime(self):
        """Resolve trading session and strategy from env and clock."""
        from morning_trading_agent.application.services.market.trading_session_resolver import (
            TradingSessionResolver,
        )

        return TradingSessionResolver(self).resolve()

    @property
    def market_hours(self):
        """Market hours parsed from environment."""
        from morning_trading_agent.domain.value_objects.market_hours import MarketHours

        return MarketHours.from_strings(
            open_time=self.app.market_open_time,
            close_time=self.app.market_close_time,
            timezone=self.app.market_timezone,
            after_market_end_time=self.app.after_market_end_time,
        )

    @property
    def catalyst_score_config(self) -> CatalystScoreConfig:
        return CatalystScoreConfig()

    @property
    def freshness_threshold_config(self) -> FreshnessThresholdConfig:
        return FreshnessThresholdConfig()

    @property
    def watchlist_quality_config(self) -> WatchlistQualityConfig:
        tp = self.trading_profile_config
        return WatchlistQualityConfig(
            min_price_inr=self.app.min_price_inr,
            min_average_volume=self.app.min_average_volume,
            min_sentiment_score=self.app.min_sentiment_score,
            min_technical_score=self.app.min_technical_score,
            min_turnover_20d_inr=tp.min_turnover_20d_inr,
            use_turnover_primary=self.app.use_turnover_primary,
        )

    @property
    def impact_weight_config(self) -> ImpactWeightConfig:
        return ImpactWeightConfig()

    @property
    def adaptive_threshold_config(self) -> AdaptiveThresholdConfig:
        return AdaptiveThresholdConfig()

    @property
    def adaptive_watchlist_config(self) -> AdaptiveWatchlistConfig:
        return AdaptiveWatchlistConfig(
            enabled=self.app.adaptive_watchlist_enabled,
            relaxed_technical_delta=self.app.relaxed_technical_delta,
            relaxed_catalyst_delta=self.app.relaxed_catalyst_delta,
            relaxed_min_tradability_indirect=self.app.relaxed_min_tradability_indirect,
        )

    @property
    def trading_profile_config(self) -> TradingProfileConfig:
        profile = TradingProfileConfig.for_profile(self.app.trading_profile)
        return profile

    @property
    def catalyst_rejection_config(self) -> CatalystRejectionConfig:
        tp = self.trading_profile_config
        return CatalystRejectionConfig(
            min_catalyst_score=self.app.min_catalyst_score,
            min_catalyst_score_without_direct_news=self.app.min_catalyst_score_no_direct_news,
            min_technical_score=self.app.min_technical_score_filter,
            min_tradability_score=self.app.min_tradability_score,
            min_materiality_score=self.app.min_materiality_score,
            min_tradability_for_indirect_news=tp.min_tradability_for_indirect_news,
            thematic_tradability_floor=self.app.thematic_tradability_floor,
            thematic_materiality_floor=self.app.thematic_materiality_floor,
            tier1_technical_override_min_catalyst=self.app.tier1_technical_override_min_catalyst,
            tier1_technical_override_min_technical=self.app.tier1_technical_override_min_technical,
            reject_bearish_for_long_watchlist=tp.reject_bearish_for_long_watchlist,
        )

    @property
    def catalyst_escalation_config(self) -> CatalystEscalationConfig:
        return CatalystEscalationConfig(
            government_procurement_crore_threshold=self.app.government_procurement_crore_threshold,
        )

    @property
    def news_quality_config(self) -> NewsQualityConfig:
        return NewsQualityConfig(
            min_article_quality=self.app.min_article_quality_score,
        )

    @property
    def near_miss_config(self) -> NearMissConfig:
        return NearMissConfig(
            min_score=self.app.near_miss_min_score,
            min_catalyst_score=self.app.near_miss_min_score,
            min_tradability_score=self.app.near_miss_min_score,
            min_materiality_score=self.app.near_miss_min_score,
        )

    @property
    def ranking_weight_config(self) -> RankingWeightConfig:
        config = RankingWeightConfig(
            catalyst=self.app.ranking_weight_catalyst,
            technical=self.app.ranking_weight_technical,
            sentiment=self.app.ranking_weight_sentiment,
            confidence=self.app.ranking_weight_confidence,
            freshness=self.app.ranking_weight_freshness,
            priority=self.app.ranking_weight_priority,
        )
        config.validate_weights()
        return config

    @property
    def technical_weight_config(self) -> TechnicalWeightConfig:
        return TechnicalWeightConfig()

    @property
    def sector_momentum_config(self) -> SectorMomentumConfig:
        return SectorMomentumConfig()

    @property
    def ingress_filter_config(self) -> IngressFilterConfig:
        return IngressFilterConfig(
            enabled=self.app.ingress_filter_enabled,
            min_ingress_score=self.app.min_ingress_score,
        )

    @property
    def beneficiary_extraction_config(self) -> BeneficiaryExtractionConfig:
        return BeneficiaryExtractionConfig()

    @property
    def ranking_weight_v3_config(self) -> RankingWeightV3Config:
        if self.app.trading_profile == "swing":
            config = swing_ranking_weight_v3()
        else:
            config = RankingWeightV3Config(
                event=self.app.ranking_v3_weight_event,
                technical=self.app.ranking_v3_weight_technical,
                liquidity=self.app.ranking_v3_weight_liquidity,
                sentiment=self.app.ranking_v3_weight_sentiment,
                freshness=self.app.ranking_v3_weight_freshness,
            )
        config.validate_weights()
        return config

    @property
    def professional_trader_gate_config(self) -> ProfessionalTraderGateConfig:
        tp = self.trading_profile_config
        app = self.app
        return ProfessionalTraderGateConfig(
            min_technical_score=app.pro_gate_min_technical_score,
            min_catalyst_strength=app.pro_gate_min_catalyst_score,
            min_final_score=app.pro_gate_min_final_score,
            min_tradeability=app.pro_gate_min_tradeability_score,
            min_freshness=app.pro_gate_min_freshness_score,
            min_expected_impact=app.pro_gate_min_impact_score,
            label_only=not tp.gate_rejects_non_trade,
            accept_watch_tag=not tp.gate_rejects_non_trade,
        )

    @property
    def tradability_score_config(self) -> TradabilityScoreConfig:
        return TradabilityScoreConfig()

    @property
    def ranking_weight_v2_config(self) -> RankingWeightV2Config:
        config = RankingWeightV2Config(
            catalyst=self.app.ranking_v2_weight_catalyst,
            magnitude=self.app.ranking_v2_weight_magnitude,
            materiality=self.app.ranking_v2_weight_materiality,
            tradability=self.app.ranking_v2_weight_tradability,
            technical=self.app.ranking_v2_weight_technical,
            sentiment=self.app.ranking_v2_weight_sentiment,
            confidence=self.app.ranking_v2_weight_confidence,
        )
        config.validate_weights()
        return config

    @property
    def catalyst_magnitude_config(self) -> CatalystMagnitudeConfig:
        return CatalystMagnitudeConfig(
            value_crore_thresholds=[
                (self.app.magnitude_value_crore_very_high, CatalystMagnitude.VERY_HIGH),
                (self.app.magnitude_value_crore_high, CatalystMagnitude.HIGH),
                (self.app.magnitude_value_crore_medium, CatalystMagnitude.MEDIUM),
                (self.app.magnitude_value_crore_low, CatalystMagnitude.LOW),
                (0.0, CatalystMagnitude.VERY_LOW),
            ],
        )

    @property
    def non_tradable_catalyst_config(self) -> NonTradableCatalystConfig:
        return NonTradableCatalystConfig(mode=self.app.non_tradable_catalyst_mode)

    @property
    def broker_rating_config(self) -> BrokerRatingConfig:
        return BrokerRatingConfig(broker_only_catalyst_score=self.app.broker_rating_score)

    @property
    def tradability_config(self) -> TradabilityConfig:
        return TradabilityConfig()

    @property
    def materiality_config(self) -> MaterialityConfig:
        return MaterialityConfig()


@lru_cache
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()
