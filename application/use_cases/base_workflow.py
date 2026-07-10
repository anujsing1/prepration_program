"""Base workflow use case."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

from morning_trading_agent.config.feature_flags import get_feature_flags
from morning_trading_agent.graph.state import TradingState
from morning_trading_agent.graph.state_adapter import StateAdapter

if TYPE_CHECKING:
    from morning_trading_agent.config.container import Container


class BaseWorkflowUseCase(ABC):
    """Shared workflow execution helpers."""

    workflow_name: str

    def __init__(self, container: Container) -> None:
        self._container = container
        self._adapter = StateAdapter()
        self._flags = get_feature_flags()

    @abstractmethod
    async def execute(
        self,
        *,
        run_date: date | None = None,
        dry_run: bool = False,
        input_artifact: Path | None = None,
        output_dir: Path | None = None,
        thread_id: str | None = None,
    ) -> TradingState:
        """Run the workflow."""

    async def _build_base_state(
        self,
        *,
        run_date: date | None,
        dry_run: bool,
    ) -> TradingState:
        startup = self._container.startup_diagnostics.collect(dry_run=dry_run)
        effective_date = run_date or self._container.resolved_runtime.reference_datetime.date()
        return StateAdapter.create_initial_state(
            run_date=effective_date,
            dry_run=dry_run or self._container.dry_run,
            debug_ranking=False,
            llm_provider=startup.active_llm_provider,
            trading_profile=self._container.settings.app.trading_profile,
        )
