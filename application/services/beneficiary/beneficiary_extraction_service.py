"""Per-article rule-based beneficiary extraction with optional LLM."""

import re

import structlog

from morning_trading_agent.application.ports.providers import LLMProvider
from morning_trading_agent.config.premarket_config import BeneficiaryExtractionConfig
from morning_trading_agent.domain.entities.article import Article, ExtractedStock, Stock
from morning_trading_agent.domain.entities.beneficiary import (
    PRIMARY_PIPELINE_ROLES,
    ROLE_DEFAULT_WEIGHT,
    ArticleStockMention,
    EntityRole,
)
from morning_trading_agent.application.services.market.canonical_symbol_service import (
    CanonicalSymbolService,
)
from morning_trading_agent.infrastructure.providers.market.symbol_resolver import SymbolResolver

_ACQUIRER_KW = ("acquires", "to acquire", "acquirer", "buying stake")
_ACQUIREE_KW = ("target company", "to be acquired", "acquiree")
_ORDER_KW = ("wins order", "bagged order", "order worth", "contract worth")
_PARTNER_KW = ("joint venture", "jv with", "partnership", "mou signed")


class BeneficiaryExtractionService:
    """Extracts primary beneficiaries per article."""

    enabled: bool = True

    def __init__(
        self,
        *,
        resolver: SymbolResolver,
        llm: LLMProvider | None = None,
        config: BeneficiaryExtractionConfig | None = None,
        canonical: CanonicalSymbolService | None = None,
    ) -> None:
        self._resolver = resolver
        self._canonical = canonical or CanonicalSymbolService(resolver)
        self._llm = llm
        self._config = config or BeneficiaryExtractionConfig()
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def extract(
        self, articles: list[Article]
    ) -> tuple[list[ArticleStockMention], dict[str, list]]:
        """Return mentions and symbol→article_id map for primaries."""
        await self._resolver.ensure_loaded()
        all_mentions: list[ArticleStockMention] = []
        symbol_articles: dict[str, list] = {}

        for article in articles:
            mentions = self._extract_from_article(article)
            if (
                not mentions
                and self._llm
                and article.ingress_scores
                and article.ingress_scores.company_relevance_score
                >= self._config.llm_crs_threshold
            ):
                llm_mentions = await self._llm_extract(article)
                mentions.extend(llm_mentions)

            primaries = [m for m in mentions if self._is_primary(m)]
            for mention in primaries:
                symbol_articles.setdefault(mention.symbol, []).append(article.id)
            all_mentions.extend(mentions)

        self._logger.info(
            "beneficiary_extraction_complete",
            articles=len(articles),
            mentions=len(all_mentions),
            primary_symbols=len(symbol_articles),
        )
        return all_mentions, symbol_articles

    async def resolve_primary_stocks(
        self, mentions: list[ArticleStockMention]
    ) -> list[Stock]:
        """Resolve primary mentions to NSE stocks."""
        primaries = [m for m in mentions if self._is_primary(m)]
        primaries.sort(key=lambda m: (m.beneficiary_rank, -m.extraction_confidence))
        extracted = [
            ExtractedStock(
                symbol=m.symbol,
                company_name=m.symbol,
                confidence=m.extraction_confidence,
            )
            for m in primaries
        ]
        return await self._canonical.resolve_batch(extracted)

    def _extract_from_article(self, article: Article) -> list[ArticleStockMention]:
        text = f"{article.title}\n{article.content[:3000]}"
        symbols = self._find_symbols(text)
        if not symbols:
            return []

        roles = self._infer_roles(text, symbols)
        mentions: list[ArticleStockMention] = []
        rank = 1
        for symbol in symbols[: self._config.max_symbols_per_article]:
            evidence = self._canonical.extraction_confidence(symbol, text)
            if not self._canonical.is_pipeline_eligible(symbol, text):
                self._logger.info(
                    "symbol_extraction_rejected",
                    article_id=str(article.id),
                    symbol=symbol,
                    evidence_confidence=evidence,
                    reason="insufficient_text_evidence",
                )
                continue
            role = roles.get(symbol, EntityRole.MENTIONED)
            weight = ROLE_DEFAULT_WEIGHT.get(role, 0.2)
            if role == EntityRole.SECTOR_PEER and not self._has_direct_tie(text, symbol):
                continue
            mentions.append(
                ArticleStockMention(
                    article_id=article.id,
                    symbol=symbol,
                    role=role,
                    beneficiary_rank=rank,
                    extraction_confidence=evidence,
                    extraction_method="rule",
                    beneficiary_weight=weight,
                )
            )
            rank += 1
        return self._re_rank_primaries(mentions)

    def _find_symbols(self, text: str) -> list[str]:
        return self._canonical.find_symbols_in_text(
            text,
            max_symbols=self._config.max_symbols_per_article,
        )

    def _infer_roles(self, text: str, symbols: list[str]) -> dict[str, EntityRole]:
        lower = text.lower()
        roles: dict[str, EntityRole] = {}
        if any(k in lower for k in _ACQUIRER_KW) and len(symbols) >= 2:
            roles[symbols[0]] = EntityRole.ACQUIRER
            roles[symbols[1]] = EntityRole.ACQUIREE
        elif any(k in lower for k in _ORDER_KW):
            roles[symbols[0]] = EntityRole.PRIMARY_BENEFICIARY
        elif any(k in lower for k in _PARTNER_KW):
            roles[symbols[0]] = EntityRole.STRATEGIC_PARTNER
        elif "sector" in lower and len(symbols) > 1:
            roles[symbols[0]] = EntityRole.PRIMARY_BENEFICIARY
            for sym in symbols[1:]:
                roles[sym] = EntityRole.SECTOR_PEER
        else:
            roles[symbols[0]] = EntityRole.PRIMARY_BENEFICIARY
        return roles

    @staticmethod
    def _has_direct_tie(text: str, symbol: str) -> bool:
        pattern = rf"\b{symbol}\b.{{0,80}}(order|contract|wins|acquires|approval)"
        return bool(re.search(pattern, text, re.IGNORECASE))

    @staticmethod
    def _re_rank_primaries(mentions: list[ArticleStockMention]) -> list[ArticleStockMention]:
        primaries = [m for m in mentions if m.role in PRIMARY_PIPELINE_ROLES]
        others = [m for m in mentions if m.role not in PRIMARY_PIPELINE_ROLES]
        primaries.sort(key=lambda m: -m.beneficiary_weight)
        for idx, mention in enumerate(primaries, start=1):
            mention.beneficiary_rank = idx
        return primaries + others

    @staticmethod
    def _is_primary(mention: ArticleStockMention) -> bool:
        return mention.beneficiary_rank == 1 or mention.role in PRIMARY_PIPELINE_ROLES

    async def _llm_extract(self, article: Article) -> list[ArticleStockMention]:
        if not self._llm:
            return []
        text = f"{article.title}\n{article.content[:3000]}"
        extracted = await self._llm.extract_stocks([article])
        mentions: list[ArticleStockMention] = []
        for item in extracted:
            symbol = item.symbol.upper()
            if not self._canonical.is_pipeline_eligible(
                symbol,
                text,
                extraction_method="llm",
                llm_confidence=item.confidence,
            ):
                self._logger.info(
                    "symbol_extraction_rejected",
                    article_id=str(article.id),
                    symbol=symbol,
                    evidence_confidence=self._canonical.extraction_confidence(symbol, text),
                    llm_confidence=item.confidence,
                    reason="llm_symbol_not_validated",
                )
                continue
            mentions.append(
                ArticleStockMention(
                    article_id=article.id,
                    symbol=symbol,
                    role=EntityRole.PRIMARY_BENEFICIARY,
                    beneficiary_rank=1,
                    extraction_confidence=max(
                        item.confidence,
                        self._canonical.extraction_confidence(symbol, text),
                    ),
                    extraction_method="llm",
                    beneficiary_weight=1.0,
                )
            )
        return mentions


class NullBeneficiaryExtractionService:
    """No-op beneficiary extraction when the feature is disabled."""

    enabled: bool = False

    def __init__(self) -> None:
        self._logger = structlog.get_logger(self.__class__.__name__)
        self._logger.warning(
            "beneficiary_extraction_disabled",
            reason="service_not_registered",
        )

    async def extract(
        self, articles: list[Article]
    ) -> tuple[list[ArticleStockMention], dict[str, list]]:
        return [], {}

    async def resolve_primary_stocks(
        self, mentions: list[ArticleStockMention]
    ) -> list[Stock]:
        return []
