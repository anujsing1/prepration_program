"""Run institutional research desk use case."""

from __future__ import annotations

from datetime import date, datetime

from morning_trading_agent.agents.research_desk.orchestrator import ResearchDeskOrchestrator
from morning_trading_agent.config.factories.research_desk_factory import ResearchDeskFactory
from morning_trading_agent.config.settings import Settings
from morning_trading_agent.domain.value_objects.research_desk import ResearchDeskMode, ResearchDeskSnapshot


class RunResearchDeskUseCase:
    """Execute the multi-agent research desk and return the executive report."""

    def __init__(self, settings: Settings, *, dry_run: bool = False, strict: bool = True) -> None:
        self._factory = ResearchDeskFactory(settings, dry_run=dry_run, strict=strict)

    async def execute(
        self,
        *,
        mode: ResearchDeskMode,
        session_date: date | None = None,
        run_at: datetime | None = None,
    ) -> ResearchDeskSnapshot:
        orchestrator = self._factory.create_orchestrator()
        return await orchestrator.run(mode=mode, session_date=session_date, run_at=run_at)
