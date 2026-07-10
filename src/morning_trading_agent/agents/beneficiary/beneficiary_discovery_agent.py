"""Beneficiary discovery agent for indirect sector beneficiaries."""

from uuid import UUID

import structlog

from morning_trading_agent.agents.beneficiary.sector_taxonomy import SectorTaxonomy
from morning_trading_agent.domain.entities.article import Article
from morning_trading_agent.domain.entities.beneficiary import (
    ArticleStockMention,
    EntityRole,
)
from morning_trading_agent.infrastructure.providers.market.symbol_resolver import SymbolResolver


class BeneficiaryDiscoveryAgent:
    """Infers sector beneficiaries from policy/commodity taxonomy (deterministic lookup)."""

    def __init__(
        self,
        *,
        resolver: SymbolResolver,
        taxonomy: SectorTaxonomy | None = None,
    ) -> None:
        self._resolver = resolver
        self._taxonomy = taxonomy or SectorTaxonomy.load()
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def discover(
        self,
        articles: list[Article],
        existing_mentions: list[ArticleStockMention],
    ) -> list[ArticleStockMention]:
        """Return additional inferred mentions not already present."""
        await self._resolver.ensure_loaded()
        existing_symbols = {m.symbol for m in existing_mentions}
        discovered: list[ArticleStockMention] = []

        for article in articles:
            text = f"{article.title}\n{article.content[:3000]}"
            for symbol, role_name, weight in self._taxonomy.match_symbols(text):
                if symbol in existing_symbols:
                    continue
                if not self._resolver.is_valid_symbol(symbol):
                    continue
                role = EntityRole.SECTOR_PEER
                if role_name == "PRIMARY_BENEFICIARY":
                    role = EntityRole.PRIMARY_BENEFICIARY
                discovered.append(
                    ArticleStockMention(
                        article_id=article.id,
                        symbol=symbol,
                        role=role,
                        beneficiary_rank=2,
                        beneficiary_weight=weight,
                        extraction_confidence=0.55,
                        extraction_method="resolver",
                    )
                )
                existing_symbols.add(symbol)

        self._logger.info(
            "beneficiary_agent_discovery",
            discovered=len(discovered),
            symbols=sorted({m.symbol for m in discovered}),
        )
        return discovered
