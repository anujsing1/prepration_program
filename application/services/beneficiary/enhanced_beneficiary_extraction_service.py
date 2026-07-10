"""Enhanced beneficiary extraction with optional discovery agent."""

from morning_trading_agent.agents.beneficiary.beneficiary_discovery_agent import (
    BeneficiaryDiscoveryAgent,
)
from morning_trading_agent.application.services.beneficiary.beneficiary_extraction_service import (
    BeneficiaryExtractionService,
)
from morning_trading_agent.domain.entities.article import Article, Stock
from morning_trading_agent.domain.entities.beneficiary import ArticleStockMention


class EnhancedBeneficiaryExtractionService(BeneficiaryExtractionService):
    """Wraps base extraction with optional beneficiary discovery agent."""

    def __init__(
        self,
        *,
        base: BeneficiaryExtractionService,
        discovery_agent: BeneficiaryDiscoveryAgent | None = None,
    ) -> None:
        self._base = base
        self._agent = discovery_agent

    async def extract(
        self, articles: list[Article]
    ) -> tuple[list[ArticleStockMention], dict[str, list]]:
        mentions, symbol_map = await self._base.extract(articles)
        if self._agent is not None:
            extra = await self._agent.discover(articles, mentions)
            for mention in extra:
                mentions.append(mention)
                if mention.beneficiary_rank == 1 or mention.role.value in (
                    "PRIMARY_BENEFICIARY",
                    "ACQUIRER",
                    "ACQUIREE",
                ):
                    symbol_map.setdefault(mention.symbol, []).append(mention.article_id)
        return mentions, symbol_map

    async def resolve_primary_stocks(
        self, mentions: list[ArticleStockMention]
    ) -> list[Stock]:
        return await self._base.resolve_primary_stocks(mentions)
