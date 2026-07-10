"""Stock Discovery Agent — validated symbols from news and corporate events."""

from __future__ import annotations

import structlog

from morning_trading_agent.agents.research_desk.base import ResearchDeskAgent
from morning_trading_agent.application.services.market.canonical_symbol_service import CanonicalSymbolService
from morning_trading_agent.domain.value_objects.agent_health import AgentHealth
from morning_trading_agent.domain.value_objects.research_desk import ResearchDeskSnapshot


class StockDiscoveryAgent(ResearchDeskAgent):
    """Aggregate validated NSE symbols for downstream technical scan."""

    name = "stock_discovery"

    def __init__(self, symbol_service: CanonicalSymbolService) -> None:
        self._symbols = symbol_service
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def run(self, snapshot: ResearchDeskSnapshot) -> ResearchDeskSnapshot:
        health = AgentHealth(agent=self.name, data_sources=["news_intelligence", "corporate_events"])
        symbol_set: set[str] = set()
        for item in snapshot.news_intelligence.articles:
            for sym in item.stocks_affected:
                if self._symbols.is_valid_symbol(sym):
                    symbol_set.add(sym)
        for event in snapshot.corporate_events.events:
            if self._symbols.is_valid_symbol(event.symbol):
                symbol_set.add(event.symbol)

        discovered = sorted(symbol_set)[:25]
        if not discovered:
            health.errors.append("No validated NSE symbols discovered")
            return self._finalize_health(snapshot, health)

        health.used_real_data = True
        health.records_processed = len(discovered)
        health.confidence = min(1.0, len(discovered) / 10.0)
        self._logger.info("stock_discovery_complete", count=len(discovered))
        snapshot = snapshot.model_copy(update={"discovered_symbols": discovered})
        return self._finalize_health(snapshot, health, outputs={"symbols": discovered})
