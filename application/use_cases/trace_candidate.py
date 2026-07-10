"""Trace a single symbol through the pipeline audit artifacts."""

from __future__ import annotations

from pathlib import Path

from morning_trading_agent.application.services.pipeline.pipeline_run_audit_service import (
    PipelineRunAuditService,
)
from morning_trading_agent.application.use_cases.generate_morning_watchlist import (
    GenerateMorningWatchlistUseCase,
)
from morning_trading_agent.config.container import Container


class TraceCandidateUseCase:
    """Runs or loads pipeline audit and prints symbol lifecycle trace."""

    def __init__(self, container: Container) -> None:
        self._container = container
        self._audit = PipelineRunAuditService()

    async def execute(
        self,
        *,
        symbol: str,
        fresh: bool = False,
        dry_run: bool = False,
        artifacts_dir: Path | None = None,
    ) -> str:
        if artifacts_dir is not None:
            self._audit = PipelineRunAuditService(artifacts_dir=artifacts_dir)

        bundle = None if fresh else self._audit.load_bundle_from_artifacts()
        if bundle is None:
            use_case = GenerateMorningWatchlistUseCase(self._container)
            state = await use_case.execute(dry_run=dry_run)
            bundle = self._audit.build(state)
            self._audit.write_artifacts(bundle)

        return self._audit.trace_symbol(bundle, symbol)
