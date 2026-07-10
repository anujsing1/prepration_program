"""Run a single modular workflow."""

from datetime import date
from pathlib import Path
from typing import cast

import structlog

from morning_trading_agent.application.use_cases.base_workflow import BaseWorkflowUseCase
from morning_trading_agent.config.container import Container
from morning_trading_agent.domain.exceptions.base import ConfigurationException
from morning_trading_agent.graph.contracts import (
    NewsWorkflowResult,
    RankingWorkflowResult,
    ResearchWorkflowResult,
    TechnicalWorkflowResult,
    WatchlistWorkflowResult,
)
from morning_trading_agent.graph.state import TradingState
from morning_trading_agent.graph.workflows.registry import WorkflowRegistry
from morning_trading_agent.infrastructure.artifacts.artifact_store import ArtifactStore


class RunWorkflowUseCase(BaseWorkflowUseCase):
    """Execute one workflow module independently."""

    def __init__(self, container: Container, workflow_name: str) -> None:
        super().__init__(container)
        self.workflow_name = workflow_name
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def execute(
        self,
        *,
        run_date: date | None = None,
        dry_run: bool = False,
        input_artifact: Path | None = None,
        output_dir: Path | None = None,
        thread_id: str | None = None,
    ) -> TradingState:
        if self.workflow_name not in WorkflowRegistry.WORKFLOW_ORDER:
            raise ValueError(f"Unknown workflow: {self.workflow_name}")

        effective_dry_run = dry_run or self._container.dry_run
        self._container.startup_diagnostics.validate_live_run(dry_run=effective_dry_run)

        state = await self._build_base_state(run_date=run_date, dry_run=effective_dry_run)
        state = self._hydrate_from_artifacts(state, input_artifact)

        use_database = self._container.settings.database_enabled and not effective_dry_run
        try:
            if use_database:
                session = await self._container.get_session()
                try:
                    orchestrator = await self._container.create_orchestrator(session)
                    result = cast(
                        TradingState,
                        await orchestrator.run_workflow(
                            self.workflow_name,
                            state,
                            thread_id=thread_id,
                        ),
                    )
                finally:
                    await session.close()
                    await self._container.dispose()
            else:
                orchestrator = await self._container.create_orchestrator(session=None)
                result = cast(
                    TradingState,
                    await orchestrator.run_workflow(
                        self.workflow_name,
                        state,
                        thread_id=thread_id,
                    ),
                )
        except ConfigurationException:
            raise

        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            self._persist_workflow_result(result, output_dir)

        return result

    def _hydrate_from_artifacts(
        self, state: TradingState, input_artifact: Path | None
    ) -> TradingState:
        if input_artifact is None:
            return state
        if not input_artifact.is_dir():
            return state

        merged = dict(state)
        loaders: list[tuple[str, type]] = [
            ("news", NewsWorkflowResult),
            ("research", ResearchWorkflowResult),
            ("technical", TechnicalWorkflowResult),
            ("ranking", RankingWorkflowResult),
            ("watchlist", WatchlistWorkflowResult),
        ]
        for name, model_type in loaders:
            path = input_artifact / f"{name}.json"
            if not path.exists():
                continue
            loaded = self._artifacts.load(path, model_type)
            kwargs = {name: loaded}
            merged = self._adapter.merge_into_trading_state(merged, **kwargs)  # type: ignore[arg-type]
        return merged  # type: ignore[return-value]

    def _persist_workflow_result(self, state: TradingState, output_dir: Path) -> None:
        store = ArtifactStore(output_dir)
        mapping = {
            "news": self._adapter.news_from_state(state),
            "research": self._adapter.research_from_state(state),
            "technical": self._adapter.technical_from_state(state),
            "ranking": self._adapter.ranking_from_state(state),
            "watchlist": self._adapter.watchlist_from_state(
                state,
                min_watchlist_size=self._container.settings.app.min_watchlist_size,
            ),
            "reporting": self._adapter.reporting_from_state(state),
        }
        idx = WorkflowRegistry.WORKFLOW_ORDER.index(self.workflow_name)
        for name in WorkflowRegistry.WORKFLOW_ORDER[: idx + 1]:
            store.save(name, mapping[name])
