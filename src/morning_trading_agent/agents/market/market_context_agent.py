"""Market context features for ranking inputs (no direct score assignment)."""

from dataclasses import dataclass

import structlog

from morning_trading_agent.domain.entities.article import Article


@dataclass(frozen=True)
class MarketContextFeatures:
    """Regime and thematic context features."""

    sector_tailwind_count: int = 0
    policy_beneficiary_count: int = 0
    macro_heavy: bool = False
    sector_bonus_cap: float = 5.0


class MarketContextAgent:
    """Extracts market context features from ingested articles."""

    _POLICY_KW = ("policy", "government", "cabinet", "mandate", "procurement", "blending")
    _MACRO_KW = ("index", "nifty", "sensex", "fed ", "inflation", "gdp")

    def __init__(self) -> None:
        self._logger = structlog.get_logger(self.__class__.__name__)

    def analyze(self, articles: list[Article]) -> MarketContextFeatures:
        sector_tailwind = 0
        policy = 0
        macro = 0
        for article in articles:
            text = f"{article.title} {article.content[:500]}".lower()
            if any(k in text for k in self._POLICY_KW):
                policy += 1
            if article.catalyst_type.value in {"SECTOR_TAILWIND", "POLICY_BENEFICIARY"}:
                sector_tailwind += 1
            if any(k in text for k in self._MACRO_KW):
                macro += 1

        features = MarketContextFeatures(
            sector_tailwind_count=sector_tailwind,
            policy_beneficiary_count=policy,
            macro_heavy=macro >= max(3, len(articles) // 4),
        )
        self._logger.info("market_context_features", **features.__dict__)
        return features

    def sector_bonus(self, features: MarketContextFeatures, *, catalyst_type: str) -> float:
        """Small bounded bonus for ranking input — never replaces deterministic score."""
        bonus = 0.0
        if catalyst_type in {"SECTOR_TAILWIND", "POLICY_BENEFICIARY", "THEMATIC_DEMAND_SURGE"}:
            bonus += min(3.0, features.policy_beneficiary_count * 0.5)
        if features.sector_tailwind_count > 0:
            bonus += min(2.0, features.sector_tailwind_count * 0.25)
        return min(features.sector_bonus_cap, bonus)
