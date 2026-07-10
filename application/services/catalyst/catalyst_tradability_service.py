"""Deterministic catalyst tradability and quality assessment."""

from __future__ import annotations

import structlog

from morning_trading_agent.domain.entities.article import Article, SentimentAnalysis, TradingCandidate
from morning_trading_agent.domain.value_objects.catalyst import CatalystType
from morning_trading_agent.domain.value_objects.pipeline_selection import WatchlistDropReason
from morning_trading_agent.config.tradability_registry import TRADABILITY_SCORE_BY_CATEGORY
from morning_trading_agent.domain.value_objects.catalyst_tradability import (
    BLOCKED_REASON_KEYWORDS,
    CATALYST_TYPE_TO_CATEGORY,
    CATEGORY_DISPLAY_NAMES,
    NON_TRADABLE_CATEGORIES,
    CatalystTradabilityCategory,
    CatalystTradabilityProfile,
    RejectedCandidateDiagnostic,
)

_EXCHANGE_COMPLIANCE_TYPES: frozenset[CatalystType] = frozenset(
    {
        CatalystType.EXCHANGE_CLARIFICATION,
        CatalystType.COMPLIANCE_FILING,
        CatalystType.CORPORATE_COMMUNICATION,
    }
)

_KEYWORD_CATEGORY_RULES: tuple[tuple[tuple[str, ...], CatalystTradabilityCategory], ...] = (
    (("voting result", "scrutinizer report"), CatalystTradabilityCategory.VOTING_RESULT),
    (("postal ballot",), CatalystTradabilityCategory.POSTAL_BALLOT),
    (("shareholder notice", "shareholder communication"), CatalystTradabilityCategory.SHAREHOLDER_NOTICE),
    (("agm notice", "annual general meeting notice"), CatalystTradabilityCategory.AGM_NOTICE),
    (("egm notice", "extraordinary general meeting notice"), CatalystTradabilityCategory.EGM_NOTICE),
    (
        ("meeting proceedings", "proceedings of", "shareholders meeting"),
        CatalystTradabilityCategory.MEETING_PROCEEDINGS,
    ),
    (
        ("compliance filing", "compliance update", "regulatory filing", "routine regulatory"),
        CatalystTradabilityCategory.COMPLIANCE_FILING,
    ),
    (("newspaper advertisement", "newspaper advert"), CatalystTradabilityCategory.NEWSPAPER_ADVERTISEMENT),
    (("exchange intimation", "exchange clarification"), CatalystTradabilityCategory.EXCHANGE_INTIMATION),
    (("record date", "record date notice"), CatalystTradabilityCategory.RECORD_DATE_NOTICE),
    (
        ("corporate governance", "governance filing"),
        CatalystTradabilityCategory.CORPORATE_GOVERNANCE_FILING,
    ),
    (("procedural update",), CatalystTradabilityCategory.ROUTINE_REGULATORY_DISCLOSURE),
    (
        ("investor presentation", "investor meet schedule"),
        CatalystTradabilityCategory.INVESTOR_PRESENTATION,
    ),
    (
        ("government contract", "govt contract", "ministry of", "public sector order"),
        CatalystTradabilityCategory.GOVT_CONTRACT,
    ),
    (("earnings beat", "beat estimates", "results beat"), CatalystTradabilityCategory.EARNINGS_BEAT),
    (("order win", "wins order", "bagged order"), CatalystTradabilityCategory.ORDER_WIN),
    (("promoter buying", "promoter stake"), CatalystTradabilityCategory.PROMOTER_BUYING),
    (("product launch", "launches product"), CatalystTradabilityCategory.PRODUCT_LAUNCH),
)


class CatalystTradabilityService:
    """Assesses catalyst tradability before scoring and candidate creation."""

    MIN_TRADABILITY_SCORE = 20.0
    MIN_QUALITY_SCORE = MIN_TRADABILITY_SCORE  # backward-compatible alias

    def __init__(self) -> None:
        self._logger = structlog.get_logger(self.__class__.__name__)

    def assess(
        self,
        sentiment: SentimentAnalysis,
        articles: list[Article],
    ) -> CatalystTradabilityProfile:
        text = self._combined_text(sentiment, articles)
        category = self._resolve_category(text, sentiment.primary_catalyst_type)
        tradability_score = self._tradability_score(category, sentiment.primary_catalyst_type)
        tradable = category not in NON_TRADABLE_CATEGORIES
        rejection_reason: str | None = None

        if sentiment.primary_catalyst_type == CatalystType.GENERIC_MENTION:
            tradable = False
            rejection_reason = "generic_mention"
        elif not sentiment.direct_company_news:
            tradable = False
            rejection_reason = "no_company_news"
        elif sentiment.primary_catalyst_type in _EXCHANGE_COMPLIANCE_TYPES:
            tradable = False
            rejection_reason = "exchange_or_compliance_noise"
        elif category in NON_TRADABLE_CATEGORIES:
            tradable = False
            rejection_reason = self._human_reason(category)
        elif tradability_score < self.MIN_TRADABILITY_SCORE:
            tradable = False
            rejection_reason = self._human_reason(category)

        profile = CatalystTradabilityProfile(
            category=category,
            tradable=tradable,
            tradability_score=tradability_score,
            rejection_reason=rejection_reason,
        )
        self._logger.debug(
            "catalyst_tradability_assessed",
            symbol=sentiment.symbol,
            category=category.value,
            tradable=tradable,
            tradability_score=tradability_score,
            rejection_reason=rejection_reason,
        )
        return profile

    @classmethod
    def filter_reason(cls, profile: CatalystTradabilityProfile | None) -> str | None:
        if profile is None:
            return None
        if profile.rejection_reason == "generic_mention":
            return "generic_mention"
        if profile.rejection_reason == "no_company_news":
            return "no_company_news"
        if profile.rejection_reason == "exchange_or_compliance_noise":
            return "exchange_or_compliance_noise"
        if not profile.tradable:
            return "non_tradable_catalyst"
        if profile.tradability_score < cls.MIN_TRADABILITY_SCORE:
            return "low_tradability_score"
        return None

    @classmethod
    def blocked_reason_text(cls, candidate: TradingCandidate) -> bool:
        text = " ".join(
            part
            for part in (
                candidate.sentiment.reason,
                candidate.sentiment.primary_catalyst_summary,
                candidate.sentiment.catalyst_tradability.rejection_reason
                if candidate.sentiment.catalyst_tradability
                else None,
            )
            if part
        ).lower()
        return any(keyword in text for keyword in BLOCKED_REASON_KEYWORDS)

    @classmethod
    def is_watchlist_safe(cls, candidate: TradingCandidate) -> bool:
        profile = candidate.sentiment.catalyst_tradability
        if profile is None:
            return not cls.blocked_reason_text(candidate)
        if not profile.tradable:
            return False
        if profile.tradability_score < cls.MIN_TRADABILITY_SCORE:
            return False
        return not cls.blocked_reason_text(candidate)

    @classmethod
    def watchlist_rejection_reason(cls, candidate: TradingCandidate) -> str | None:
        """Return a watchlist drop reason when candidate fails tradability gate."""
        profile = candidate.sentiment.catalyst_tradability
        if profile is None:
            if cls.blocked_reason_text(candidate):
                return WatchlistDropReason.TRADABILITY_POLICY_REJECTED.value
            return None
        if not profile.tradable or cls.blocked_reason_text(candidate):
            return WatchlistDropReason.TRADABILITY_POLICY_REJECTED.value
        if profile.tradability_score < cls.MIN_TRADABILITY_SCORE:
            return WatchlistDropReason.TRADABILITY_SCORE_FLOOR.value
        return None

    def to_diagnostic(
        self,
        sentiment: SentimentAnalysis,
        *,
        rejection_code: str | None = None,
    ) -> RejectedCandidateDiagnostic:
        profile = sentiment.catalyst_tradability
        if profile is None:
            profile = self.assess(sentiment, [])
        reason = profile.rejection_reason or rejection_code or "non_tradable_catalyst"
        return RejectedCandidateDiagnostic(
            symbol=sentiment.symbol,
            catalyst_type=sentiment.primary_catalyst_type.value,
            tradable=profile.tradable,
            tradability_score=profile.tradability_score,
            rejection_reason=reason,
        )

    def _resolve_category(
        self,
        text: str,
        catalyst_type: CatalystType,
    ) -> CatalystTradabilityCategory:
        lower = text.lower()
        for keywords, category in _KEYWORD_CATEGORY_RULES:
            if any(keyword in lower for keyword in keywords):
                return category

        if catalyst_type == CatalystType.BOARD_MEETING:
            if "agm" in lower:
                return CatalystTradabilityCategory.AGM_NOTICE
            if "egm" in lower or "extraordinary" in lower:
                return CatalystTradabilityCategory.EGM_NOTICE
            if "proceedings" in lower or "meeting held" in lower:
                return CatalystTradabilityCategory.MEETING_PROCEEDINGS
            return CatalystTradabilityCategory.AGM_NOTICE

        if catalyst_type == CatalystType.CORPORATE_ACTION:
            if any(kw in lower for kw in ("proceedings", "meeting held", "shareholders meeting")):
                return CatalystTradabilityCategory.MEETING_PROCEEDINGS
            if "postal ballot" in lower:
                return CatalystTradabilityCategory.POSTAL_BALLOT

        return CATALYST_TYPE_TO_CATEGORY.get(catalyst_type, CatalystTradabilityCategory.OTHER)

    @staticmethod
    def _tradability_score(
        category: CatalystTradabilityCategory,
        catalyst_type: CatalystType,
    ) -> float:
        if category in TRADABILITY_SCORE_BY_CATEGORY:
            return TRADABILITY_SCORE_BY_CATEGORY[category]
        mapped = CATALYST_TYPE_TO_CATEGORY.get(catalyst_type)
        if mapped and mapped in TRADABILITY_SCORE_BY_CATEGORY:
            return TRADABILITY_SCORE_BY_CATEGORY[mapped]
        return TRADABILITY_SCORE_BY_CATEGORY[CatalystTradabilityCategory.OTHER]

    @staticmethod
    def _human_reason(category: CatalystTradabilityCategory) -> str:
        return CATEGORY_DISPLAY_NAMES.get(
            category,
            category.value.replace("_", " ").title(),
        )

    @staticmethod
    def _combined_text(sentiment: SentimentAnalysis, articles: list[Article]) -> str:
        parts = [sentiment.primary_catalyst_summary, sentiment.reason]
        article_map = {article.id: article for article in articles}
        for article_id in sentiment.article_ids:
            article = article_map.get(article_id)
            if article:
                parts.append(f"{article.title} {article.content}")
        return " ".join(part for part in parts if part)
