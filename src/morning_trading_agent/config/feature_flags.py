"""Feature flags for modular workflow migration."""

import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from morning_trading_agent.config.settings import _ENV_FILE


class FeatureFlags(BaseSettings):
    """Runtime feature flags."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    use_modular_workflow: bool = Field(default=True, alias="USE_MODULAR_WORKFLOW")
    use_workflow_contracts: bool = Field(default=True, alias="USE_WORKFLOW_CONTRACTS")
    enable_workflow_cli: bool = Field(default=True, alias="ENABLE_WORKFLOW_CLI")
    enable_checkpointing: bool = Field(default=False, alias="ENABLE_CHECKPOINTING")
    enable_beneficiary_agent: bool = Field(default=False, alias="ENABLE_BENEFICIARY_AGENT")
    enable_catalyst_verifier: bool = Field(default=False, alias="ENABLE_CATALYST_VERIFIER")
    enable_db_catalyst_taxonomy: bool = Field(default=False, alias="ENABLE_DB_CATALYST_TAXONOMY")
    enable_catalyst_reclassification: bool = Field(default=True, alias="ENABLE_CATALYST_RECLASSIFICATION")
    enable_market_context: bool = Field(default=False, alias="ENABLE_MARKET_CONTEXT")
    enable_catalyst_rag: bool = Field(default=True, alias="ENABLE_CATALYST_RAG")
    log_format: str = Field(default="console", alias="LOG_FORMAT")


def get_feature_flags() -> FeatureFlags:
    """Load feature flags from environment."""
    return FeatureFlags()
