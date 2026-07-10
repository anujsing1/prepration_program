"""Factory for research desk agents and orchestrator."""

from __future__ import annotations

from pathlib import Path

from morning_trading_agent.agents.research_desk.corporate_event_agent import CorporateEventAgent
from morning_trading_agent.agents.research_desk.executive_summary_agent import ExecutiveSummaryAgent
from morning_trading_agent.agents.research_desk.global_market_agent import GlobalMarketAgent
from morning_trading_agent.agents.research_desk.historical_context_agent import HistoricalContextAgent
from morning_trading_agent.agents.research_desk.institutional_flow_agent import InstitutionalFlowAgent
from morning_trading_agent.agents.research_desk.market_regime_agent import MarketRegimeAgent
from morning_trading_agent.agents.research_desk.market_structure_agent import MarketStructureAgent
from morning_trading_agent.agents.research_desk.memory_rag_agent import MemoryRagAgent
from morning_trading_agent.agents.research_desk.news_intelligence_agent import NewsIntelligenceAgent
from morning_trading_agent.agents.research_desk.options_flow_agent import OptionsFlowAgent
from morning_trading_agent.agents.research_desk.orchestrator import ResearchDeskOrchestrator
from morning_trading_agent.agents.research_desk.portfolio_construction_agent import PortfolioConstructionAgent
from morning_trading_agent.agents.research_desk.prediction_validation_agent import PredictionValidationAgent
from morning_trading_agent.agents.research_desk.risk_management_agent import RiskManagementAgent
from morning_trading_agent.agents.research_desk.scoring_agent import ScoringAgent
from morning_trading_agent.agents.research_desk.sector_rotation_agent import SectorRotationAgent
from morning_trading_agent.agents.research_desk.stock_discovery_agent import StockDiscoveryAgent
from morning_trading_agent.agents.research_desk.technical_analysis_agent import TechnicalAnalysisDeskAgent
from morning_trading_agent.application.services.market.canonical_symbol_service import CanonicalSymbolService
from morning_trading_agent.application.services.memory.market_memory_index import MarketMemoryIndex
from morning_trading_agent.application.services.memory.market_memory_store import MarketMemoryStore
from morning_trading_agent.application.services.rag.embedding_provider import (
    KeywordEmbeddingProvider,
    create_embedding_provider,
)
from morning_trading_agent.application.services.research_desk.observability import ResearchDeskObservability
from morning_trading_agent.application.services.research_desk.research_market_data_service import (
    ResearchMarketDataService,
)
from morning_trading_agent.config.factories.provider_factory import ProviderFactory
from morning_trading_agent.config.settings import Settings
from morning_trading_agent.infrastructure.providers.market.symbol_resolver import SymbolResolver


class ResearchDeskFactory:
    """Wire research desk agents from application settings."""

    def __init__(self, settings: Settings, *, dry_run: bool = False, strict: bool = True) -> None:
        self._settings = settings
        self._dry_run = dry_run
        self._strict = strict
        self._provider_factory = ProviderFactory(settings)

    def create_orchestrator(self) -> ResearchDeskOrchestrator:
        memory_root = Path(self._settings.market_memory.root_path)
        store = MarketMemoryStore(memory_root)
        cache_path = memory_root / "index" / "embedding_cache.json"
        index = MarketMemoryIndex(store, cache_path=cache_path)
        embedder = (
            KeywordEmbeddingProvider()
            if self._dry_run
            else create_embedding_provider(
                self._settings,
                provider_name=self._settings.app.llm_provider,
                embedding_model=self._settings.rag.embedding_model,
            )
        )
        memory_agent = MemoryRagAgent(store, index, embedder)
        market_data = ResearchMarketDataService(
            lookback_days=self._settings.app.technical_lookback_days,
        )
        symbol_service = CanonicalSymbolService(SymbolResolver())
        news = self._provider_factory.create_news_aggregator_service(
            resolved_runtime=self._settings.resolved_runtime,
        )
        observability = ResearchDeskObservability()

        agents = _build_agents(
            market_data=market_data,
            news=news,
            symbol_service=symbol_service,
            index=index,
            memory_store=store,
            max_watchlist=self._settings.app.max_watchlist_size,
            fetch_limit=self._settings.app.news_fetch_limit,
            top_k=self._settings.market_memory.top_k,
        )

        postmarket_chain = [
            agents["market_structure"],
            agents["prediction_validation"],
            agents["sector_rotation"],
            agents["institutional_flow"],
            agents["global_market"],
            agents["options_flow"],
            agents["market_regime"],
            agents["news_intelligence"],
            agents["corporate_event"],
            agents["stock_discovery"],
            agents["technical_analysis"],
            agents["historical_context"],
            agents["scoring"],
            agents["portfolio_construction"],
            agents["risk_management"],
            agents["executive_summary"],
        ]

        premarket_chain = [
            agents["global_market"],
            agents["market_structure"],
            agents["prediction_validation"],
            agents["news_intelligence"],
            agents["corporate_event"],
            agents["stock_discovery"],
            agents["technical_analysis"],
            agents["sector_rotation"],
            agents["institutional_flow"],
            agents["options_flow"],
            agents["market_regime"],
            agents["historical_context"],
            agents["scoring"],
            agents["portfolio_construction"],
            agents["risk_management"],
            agents["executive_summary"],
        ]

        critical_agents = {
            "market_structure",
            "sector_rotation",
            "institutional_flow",
            "global_market",
            "options_flow",
            "scoring",
            "portfolio_construction",
        }
        for agent in agents.values():
            if hasattr(agent, "strict"):
                agent.strict = self._strict and agent.name in critical_agents

        return ResearchDeskOrchestrator(
            postmarket_agents=postmarket_chain,
            premarket_agents=premarket_chain,
            memory_agent=memory_agent,
            observability=observability,
            market_data=market_data,
        )


def _build_agents(
    *,
    market_data: ResearchMarketDataService,
    news,
    symbol_service: CanonicalSymbolService,
    index: MarketMemoryIndex,
    memory_store: MarketMemoryStore,
    max_watchlist: int,
    fetch_limit: int,
    top_k: int,
) -> dict[str, object]:
    return {
        "market_structure": MarketStructureAgent(market_data),
        "sector_rotation": SectorRotationAgent(market_data),
        "institutional_flow": InstitutionalFlowAgent(market_data),
        "global_market": GlobalMarketAgent(market_data),
        "options_flow": OptionsFlowAgent(market_data),
        "market_regime": MarketRegimeAgent(),
        "prediction_validation": PredictionValidationAgent(memory_store),
        "news_intelligence": NewsIntelligenceAgent(news, symbol_service, fetch_limit=fetch_limit),
        "corporate_event": CorporateEventAgent(symbol_service),
        "stock_discovery": StockDiscoveryAgent(symbol_service),
        "technical_analysis": TechnicalAnalysisDeskAgent(market_data),
        "historical_context": HistoricalContextAgent(index, top_k=top_k),
        "scoring": ScoringAgent(),
        "portfolio_construction": PortfolioConstructionAgent(max_long=max_watchlist),
        "risk_management": RiskManagementAgent(),
        "executive_summary": ExecutiveSummaryAgent(),
    }
