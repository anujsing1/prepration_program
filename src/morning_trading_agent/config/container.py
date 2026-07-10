"""Dependency injection composition root."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime

from langgraph.graph.state import CompiledStateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from morning_trading_agent.application.services.catalyst.catalyst_classification_service import (
    CatalystClassificationService,
)
from morning_trading_agent.application.services.catalyst.catalyst_scoring_service import (
    CatalystScoringService,
)
from morning_trading_agent.application.services.startup_diagnostics import StartupDiagnosticsService
from morning_trading_agent.config.factories.llm_factory import LLMFactory
from morning_trading_agent.config.factories.provider_factory import ProviderFactory
from morning_trading_agent.config.factories.strategy_factory import StrategyFactory
from morning_trading_agent.config.factories.workflow_factory import WorkflowFactory
from morning_trading_agent.config.feature_flags import get_feature_flags
from morning_trading_agent.config.runtime_overrides import RuntimeOverrides, apply_runtime_overrides
from morning_trading_agent.config.settings import Settings, get_settings
from morning_trading_agent.graph.master.orchestrator import MasterWorkflowOrchestrator
from morning_trading_agent.graph.state import TradingState
from morning_trading_agent.graph.trading_graph import TradingGraphBuilder
from morning_trading_agent.infrastructure.database.session import DatabaseSessionFactory
from morning_trading_agent.infrastructure.http.ssl_setup import configure_ssl_certificates
from morning_trading_agent.infrastructure.logging.setup import configure_logging
from morning_trading_agent.infrastructure.providers.market.symbol_resolver import SymbolResolver


class Container:
    """Composition root wiring all application dependencies."""

    def __init__(
        self,
        settings: Settings | None = None,
        *,
        dry_run: bool = False,
        session: str | None = None,
        run_at: datetime | None = None,
    ) -> None:
        configure_ssl_certificates()
        base_settings = settings or get_settings()
        overrides = RuntimeOverrides(session=session, run_at=run_at)
        self.settings = apply_runtime_overrides(base_settings, overrides)
        self.resolved_runtime = self.settings.resolved_runtime
        self.dry_run = dry_run or self.settings.app.dry_run
        flags = get_feature_flags()
        configure_logging(self.settings.app.log_level, log_format=flags.log_format)
        self._db_factory = DatabaseSessionFactory(self.settings)
        self._provider_factory = ProviderFactory(self.settings)
        self._llm_factory = LLMFactory(self.settings)
        self._strategy_factory = StrategyFactory(self.settings)
        self._symbol_resolver = SymbolResolver()
        self._catalyst_scoring = CatalystScoringService(
            score_config=self.settings.catalyst_score_config
        )
        self._catalyst_classification = CatalystClassificationService(
            scoring_service=self._catalyst_scoring
        )
        self._workflow_factory = WorkflowFactory(
            self.settings,
            dry_run=self.dry_run,
            provider_factory=self._provider_factory,
            llm_factory=self._llm_factory,
            strategy_factory=self._strategy_factory,
            catalyst_classification=self._catalyst_classification,
            symbol_resolver=self._symbol_resolver,
        )
        self.startup_diagnostics = StartupDiagnosticsService(self.settings)
        self._checkpointer = None

    async def create_graph(
        self, session: AsyncSession | None = None
    ) -> CompiledStateGraph[TradingState, None, TradingState, TradingState]:
        """Build compiled LangGraph workflow (legacy API)."""
        orchestrator = await self.create_orchestrator(session)
        return orchestrator.build_graph()

    async def create_orchestrator(
        self, session: AsyncSession | None = None
    ) -> MasterWorkflowOrchestrator:
        """Build master workflow orchestrator."""
        node_factory = await self.create_node_factory(session)
        checkpointer = await self._get_checkpointer()
        return MasterWorkflowOrchestrator(
            node_factory,
            checkpointer=checkpointer,
        )

    async def create_node_factory(
        self, session: AsyncSession | None = None
    ):
        """Build node factory for workflow or debug execution."""
        return await self._workflow_factory.create_node_factory(session)

    async def _get_checkpointer(self) -> object | None:
        flags = get_feature_flags()
        if not flags.enable_checkpointing:
            return None
        if self._checkpointer is not None:
            return self._checkpointer
        from morning_trading_agent.infrastructure.checkpointing.postgres_checkpointer import (
            create_postgres_checkpointer,
        )

        self._checkpointer = await create_postgres_checkpointer(self.settings)
        return self._checkpointer

    @asynccontextmanager
    async def session_scope(self) -> AsyncIterator[AsyncSession]:
        """Yield a session that is closed before engine disposal."""
        async with self._db_factory._session_factory() as session:
            yield session

    async def get_session(self) -> AsyncSession:
        """Create a new async database session."""
        session_factory = self._db_factory._session_factory
        return session_factory()

    async def dispose(self) -> None:
        """Cleanup resources."""
        await self._db_factory.dispose()
