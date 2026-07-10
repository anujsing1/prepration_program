"""Ranking strategy factory."""

from morning_trading_agent.application.ranking.institutional_ranking_strategy import (
    InstitutionalRankingStrategy,
)
from morning_trading_agent.application.ranking.institutional_ranking_strategy_v4 import (
    InstitutionalRankingStrategyV4,
)
from morning_trading_agent.application.ranking.premarket_quality_strategy import (
    PremarketQualityRankingStrategy,
)
from morning_trading_agent.application.ranking.strategies import (
    HybridRankingStrategy,
    MomentumRankingStrategy,
    NewsDrivenRankingStrategy,
    PremarketHybridRankingStrategy,
    RankingStrategy,
)
from morning_trading_agent.config.settings import Settings
from morning_trading_agent.config.feature_flags import get_feature_flags


class StrategyFactory:
    """Creates ranking strategy instances."""

    _STRATEGIES: dict[str, type[RankingStrategy]] = {
        "premarket_hybrid": PremarketHybridRankingStrategy,
        "premarket_hybrid_v2": PremarketQualityRankingStrategy,
        "premarket_institutional_v3": InstitutionalRankingStrategy,
        "premarket_institutional_v4": InstitutionalRankingStrategyV4,
        "intraday_momentum_v1": MomentumRankingStrategy,
        "postmarket_review_v1": HybridRankingStrategy,
        "hybrid": HybridRankingStrategy,
        "news": NewsDrivenRankingStrategy,
        "momentum": MomentumRankingStrategy,
    }

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def create_ranking_strategy(self, strategy_name: str | None = None) -> RankingStrategy:
        """Create ranking strategy from resolved session or explicit name."""
        name = strategy_name or self._settings.resolved_runtime.effective_strategy
        if name == "premarket_hybrid":
            return PremarketHybridRankingStrategy(
                weight_config=self._settings.ranking_weight_config
            )
        if name == "premarket_hybrid_v2":
            return PremarketQualityRankingStrategy(
                weight_config=self._settings.ranking_weight_v2_config
            )
        if name == "premarket_institutional_v3":
            return InstitutionalRankingStrategy(
                weight_config=self._settings.ranking_weight_v3_config,
                base_builder=PremarketQualityRankingStrategy(
                    weight_config=self._settings.ranking_weight_v2_config
                ),
            )
        if name == "premarket_institutional_v4":
            from morning_trading_agent.agents.market.market_context_agent import (
                MarketContextFeatures,
            )

            v3 = InstitutionalRankingStrategy(
                weight_config=self._settings.ranking_weight_v3_config,
                base_builder=PremarketQualityRankingStrategy(
                    weight_config=self._settings.ranking_weight_v2_config
                ),
            )
            features = None
            if get_feature_flags().enable_market_context:
                features = MarketContextFeatures()
            return InstitutionalRankingStrategyV4(v3_strategy=v3, market_features=features)
        strategy_cls = self._STRATEGIES.get(name, InstitutionalRankingStrategy)
        if strategy_cls is InstitutionalRankingStrategy:
            return InstitutionalRankingStrategy(
                weight_config=self._settings.ranking_weight_v3_config
            )
        if strategy_cls is PremarketQualityRankingStrategy:
            return PremarketQualityRankingStrategy(
                weight_config=self._settings.ranking_weight_v2_config
            )
        if strategy_cls is PremarketHybridRankingStrategy:
            return PremarketHybridRankingStrategy(
                weight_config=self._settings.ranking_weight_config
            )
        return strategy_cls()
