"""Generate morning watchlist use case."""

from datetime import UTC, date, datetime
from typing import cast

import structlog

from morning_trading_agent.application.builders.pending_catalyst_report_builder import (
    PendingCatalystReportBuilder,
)
from morning_trading_agent.application.builders.ranking_debug_report_builder import (
    RankingDebugReportBuilder,
)
from morning_trading_agent.application.services.pipeline.pipeline_diagnostics_service import (
    PipelineDiagnosticsService,
)
from morning_trading_agent.application.services.pipeline.pipeline_forensics_service import (
    PipelineForensicsService,
)
from morning_trading_agent.application.services.pipeline.pipeline_run_audit_service import (
    PipelineRunAuditService,
)
from morning_trading_agent.application.services.pipeline.ranking_forensics_service import (
    RankingForensicsService,
)
from morning_trading_agent.application.services.pipeline.trading_usefulness_audit_service import (
    TradingUsefulnessAuditService,
)
from morning_trading_agent.application.services.pipeline.watchlist_selection_forensics_service import (
    WatchlistSelectionForensicsService,
)
from morning_trading_agent.application.services.workflow_diagnostics import WorkflowDiagnosticsService
from morning_trading_agent.config.container import Container
from morning_trading_agent.domain.exceptions.base import ConfigurationException
from morning_trading_agent.graph.state import TradingState
from morning_trading_agent.graph.state_adapter import StateAdapter
from morning_trading_agent.infrastructure.llm.llm_telemetry import get_llm_telemetry, reset_llm_telemetry


class GenerateMorningWatchlistUseCase:
    """Orchestrates the morning trading workflow."""

    def __init__(self, container: Container) -> None:
        self._container = container
        self._logger = structlog.get_logger(self.__class__.__name__)
        self._startup_diagnostics = container.startup_diagnostics
        self._workflow_diagnostics = WorkflowDiagnosticsService()
        self._pipeline_diagnostics = PipelineDiagnosticsService()
        self._pipeline_run_audit = PipelineRunAuditService()
        self._pipeline_forensics = PipelineForensicsService()
        self._trading_usefulness_audit = TradingUsefulnessAuditService(
            artifacts_dir=self._pipeline_run_audit._artifacts_dir,
        )
        self._ranking_forensics = RankingForensicsService(
            settings=container.settings,
            artifacts_dir=self._pipeline_run_audit._artifacts_dir,
        )
        self._watchlist_forensics = WatchlistSelectionForensicsService(
            quality_config=container.settings.watchlist_quality_config,
            profile=container.settings.trading_profile_config,
            max_watchlist_size=container.settings.app.max_watchlist_size,
            min_watchlist_size=container.settings.app.min_watchlist_size,
        )
        self._adapter = StateAdapter()

    async def execute(
        self,
        *,
        run_date: date | None = None,
        dry_run: bool = False,
        debug_ranking: bool = False,
        thread_id: str | None = None,
        resume: bool = False,
    ) -> TradingState:
        """Run the full morning watchlist generation workflow."""
        effective_date = run_date or self._resolve_run_date()
        effective_dry_run = dry_run or self._container.dry_run
        use_database = self._container.settings.database_enabled and not effective_dry_run

        self._startup_diagnostics.validate_live_run(dry_run=effective_dry_run)
        startup = self._startup_diagnostics.collect(dry_run=effective_dry_run)
        self._startup_diagnostics.log(startup)
        reset_llm_telemetry()

        self._logger.info(
            "workflow_start",
            run_date=str(effective_date),
            dry_run=effective_dry_run,
            database=use_database,
            telegram=self._container.settings.telegram_enabled and not effective_dry_run,
            llm_provider=startup.active_llm_provider,
            resume=resume,
        )

        initial_state = self._adapter.create_initial_state(
            run_date=effective_date,
            dry_run=effective_dry_run,
            debug_ranking=debug_ranking,
            llm_provider=startup.active_llm_provider,
            trading_profile=self._container.settings.app.trading_profile,
        )
        initial_state["effective_strategy"] = (
            self._container.settings.resolved_runtime.effective_strategy
        )

        effective_thread_id = thread_id or f"{effective_date.isoformat()}_morning"

        try:
            if use_database:
                session = await self._container.get_session()
                try:
                    orchestrator = await self._container.create_orchestrator(session)
                    result = cast(
                        TradingState,
                        await orchestrator.run_full_pipeline(
                            initial_state,
                            thread_id=effective_thread_id if resume else None,
                        ),
                    )
                finally:
                    await session.close()
                    await self._container.dispose()
            else:
                orchestrator = await self._container.create_orchestrator(session=None)
                result = cast(
                    TradingState,
                    await orchestrator.run_full_pipeline(
                        initial_state,
                        thread_id=effective_thread_id if resume else None,
                    ),
                )
        except ConfigurationException:
            raise
        except Exception as exc:
            self._logger.error("workflow_failed", error=str(exc))
            initial_state["errors"].append(str(exc))
            result = initial_state

        diagnostic = self._workflow_diagnostics.build(
            result,
            llm_provider=result.get("llm_provider", startup.active_llm_provider),
            min_watchlist_size=self._container.settings.app.min_watchlist_size,
        )
        pipeline_report = self._pipeline_diagnostics.build(result)
        result["pipeline_diagnostics_report"] = pipeline_report.model_dump()
        self._logger.info(
            "pipeline_diagnostics_complete",
            **pipeline_report.to_log_dict(),
        )

        audit_bundle = None
        try:
            audit_bundle = self._pipeline_run_audit.build(result)
            self._pipeline_run_audit.write_artifacts(audit_bundle)
            self._pipeline_run_audit.print_runtime_diagnostics(audit_bundle)
            result["pipeline_run_audit"] = audit_bundle.report.model_dump(mode="json")
        except Exception as exc:
            self._logger.error("audit_generation_failed", error=str(exc), exc_info=True)
            result["errors"].append(f"audit_generation_failed: {exc}")

        try:
            forensics_md = self._watchlist_forensics.build_markdown(result)
            forensics_path = (
                self._pipeline_run_audit._artifacts_dir / "watchlist_selection_forensics.md"
            )
            forensics_path.write_text(forensics_md, encoding="utf-8")
            self._logger.info(
                "watchlist_selection_forensics_written",
                path=str(forensics_path),
            )
        except Exception as exc:
            self._logger.error("audit_generation_failed", artifact="watchlist_forensics", error=str(exc))
            result["errors"].append(f"watchlist_forensics_failed: {exc}")

        try:
            forensic_paths = await self._pipeline_forensics.write_all(result)
            self._logger.info(
                "pipeline_forensics_written",
                paths={k: str(v) for k, v in forensic_paths.items()},
            )
        except Exception as exc:
            self._logger.error("audit_generation_failed", artifact="pipeline_forensics", error=str(exc))
            result["errors"].append(f"pipeline_forensics_failed: {exc}")

        if audit_bundle is not None:
            try:
                usefulness_paths = self._trading_usefulness_audit.write_all(result, audit_bundle)
                self._trading_usefulness_audit.print_console_summary(result, audit_bundle)
                self._logger.info(
                    "trading_usefulness_audit_written",
                    paths={k: str(v) for k, v in usefulness_paths.items()},
                )
            except Exception as exc:
                self._logger.error(
                    "audit_generation_failed",
                    artifact="trading_usefulness_audit",
                    error=str(exc),
                )
                result["errors"].append(f"trading_usefulness_audit_failed: {exc}")

        try:
            ranking_forensics_path = self._ranking_forensics.write_and_summarize(result)
            self._logger.info("ranking_forensics_written", path=str(ranking_forensics_path))
        except Exception as exc:
            self._logger.error("audit_generation_failed", artifact="ranking_forensics", error=str(exc))
            result["errors"].append(f"ranking_forensics_failed: {exc}")

        self._logger.info("workflow_diagnostic_report", **diagnostic.to_log_dict())

        if result.get("report"):
            parts = [result["report"].markdown]
            pending_section = PendingCatalystReportBuilder().build(
                result.get("pending_catalysts_discovered", [])
            )
            if pending_section:
                parts.append(pending_section)
            if not effective_dry_run:
                parts.append(diagnostic.to_markdown())
            if debug_ranking:
                debug_report = RankingDebugReportBuilder().build(result)
                self._logger.info(
                    "ranking_debug_report",
                    trace_count=len(result.get("pipeline_traces", [])),
                )
                parts.append(debug_report)
                metadata = dict(result["report"].metadata)
                metadata["debug_ranking"] = True
                result["report"] = result["report"].model_copy(
                    update={"markdown": "\n\n".join(parts), "metadata": metadata}
                )
            elif not effective_dry_run:
                result["report"] = result["report"].model_copy(
                    update={"markdown": "\n\n".join(parts)}
                )

        self._logger.info(
            "workflow_complete",
            candidates=len(result["ranked_candidates"]),
            errors=len(result["errors"]),
        )
        self._logger.info("llm_telemetry_summary", **get_llm_telemetry().summary())
        return result

    def _resolve_run_date(self) -> date:
        runtime = self._container.resolved_runtime
        override = self._container.settings.app.run_datetime_override.strip()
        if override:
            return runtime.reference_datetime.date()
        return datetime.now(UTC).date()
