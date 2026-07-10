"""Run pipeline debug stages with structured diagnostics."""

from datetime import date
from pathlib import Path

import structlog

from morning_trading_agent.application.services.pipeline.pipeline_debug_runner import (
    PipelineDebugRunner,
)
from morning_trading_agent.config.container import Container
from morning_trading_agent.domain.value_objects.pipeline_debug import PipelineDebugReport
from morning_trading_agent.graph.state import TradingState
from morning_trading_agent.graph.state_adapter import StateAdapter


class DebugPipelineUseCase:
    """Execute debug pipeline stages independently."""

    def __init__(self, container: Container) -> None:
        self._container = container
        self._adapter = StateAdapter()
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def execute(
        self,
        *,
        run_date: date | None = None,
        dry_run: bool = True,
        stages: list[str] | None = None,
        output_dir: Path | None = None,
    ) -> tuple[TradingState, PipelineDebugReport]:
        effective_dry_run = dry_run or self._container.dry_run
        self._container.startup_diagnostics.validate_live_run(dry_run=effective_dry_run)
        startup = self._container.startup_diagnostics.collect(dry_run=effective_dry_run)
        self._container.startup_diagnostics.log(startup)

        state = self._adapter.create_initial_state(
            run_date=run_date or date.today(),
            dry_run=effective_dry_run,
            debug_ranking=True,
            llm_provider=startup.active_llm_provider,
            trading_profile=self._container.settings.app.trading_profile,
        )
        state["pipeline_debug"] = True
        state["pipeline_debug_summaries"] = []

        node_factory = await self._container.create_node_factory(None)
        runner = PipelineDebugRunner(node_factory)
        report = await runner.run(state, stages=stages)

        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            report_path = output_dir / "pipeline_debug_report.md"
            report_path.write_text(report.to_markdown(), encoding="utf-8")
            self._logger.info("pipeline_debug_report_written", path=str(report_path))

        return state, report
