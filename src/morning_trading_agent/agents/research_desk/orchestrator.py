"""Research Desk Orchestrator — coordinates multi-agent institutional workflow."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

import structlog

from morning_trading_agent.agents.research_desk.base import ResearchDeskAgent
from morning_trading_agent.agents.research_desk.memory_rag_agent import MemoryRagAgent
from morning_trading_agent.application.services.research_desk.observability import ResearchDeskObservability
from morning_trading_agent.application.services.research_desk.research_market_data_service import (
    ResearchMarketDataService,
)
from morning_trading_agent.domain.value_objects.research_desk import ResearchDeskMode, ResearchDeskSnapshot, ThesisValidation


class ResearchDeskOrchestrator:
    """Run postmarket or premarket agent pipelines with health validation."""

    def __init__(
        self,
        *,
        postmarket_agents: list[ResearchDeskAgent],
        premarket_agents: list[ResearchDeskAgent],
        memory_agent: MemoryRagAgent,
        observability: ResearchDeskObservability | None = None,
        market_data: ResearchMarketDataService | None = None,
    ) -> None:
        self._postmarket_agents = postmarket_agents
        self._premarket_agents = premarket_agents
        self._memory = memory_agent
        self._observability = observability or ResearchDeskObservability()
        self._market_data = market_data
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def run(
        self,
        *,
        mode: ResearchDeskMode,
        session_date: date | None = None,
        run_at: datetime | None = None,
    ) -> ResearchDeskSnapshot:
        """Execute the full research desk pipeline for the given mode."""
        now = run_at or datetime.now(UTC)
        session = session_date or now.date()
        snapshot = ResearchDeskSnapshot(
            run_id=str(uuid.uuid4()),
            mode=mode,
            session_date=session,
            run_at=now,
            metadata={"_observability": self._observability},
        )

        try:
            if mode == ResearchDeskMode.PREMARKET:
                snapshot = await self._run_premarket(snapshot)
            else:
                snapshot = await self._run_postmarket(snapshot)
            snapshot = await self._memory.run(snapshot)
        finally:
            artifact_paths = self._observability.write_artifacts(run_id=snapshot.run_id)
            snapshot.metadata["observability_artifacts"] = artifact_paths
            if self._market_data is not None:
                await self._market_data.close()

        return snapshot

    async def _run_chain(
        self, snapshot: ResearchDeskSnapshot, agents: list[ResearchDeskAgent]
    ) -> ResearchDeskSnapshot:
        for agent in agents:
            self._logger.info("research_desk_agent_start", agent=agent.name)
            snapshot = await agent.run(snapshot)
            self._logger.info("research_desk_agent_complete", agent=agent.name)
        return snapshot

    async def _run_postmarket(self, snapshot: ResearchDeskSnapshot) -> ResearchDeskSnapshot:
        self._logger.info("research_desk_postmarket_start", run_id=snapshot.run_id)
        return await self._run_chain(snapshot, self._postmarket_agents)

    async def _run_premarket(self, snapshot: ResearchDeskSnapshot) -> ResearchDeskSnapshot:
        self._logger.info("research_desk_premarket_start", run_id=snapshot.run_id)
        prior = self._memory.load_previous(snapshot)
        if prior is not None:
            snapshot.metadata["prior_memory_date"] = prior.date.isoformat()
            snapshot.metadata["prior_memory"] = prior
            snapshot.thesis_validation = ThesisValidation(
                prior_date=prior.date.isoformat(),
                prior_thesis=prior.executive_summary[:500] if prior.executive_summary else "",
            )

        for agent in self._premarket_agents:
            self._logger.info("research_desk_agent_start", agent=agent.name)
            snapshot = await agent.run(snapshot)
            if agent.name == "stock_discovery" and prior is not None:
                snapshot = _refresh_thesis_validation(prior, snapshot)
            self._logger.info("research_desk_agent_complete", agent=agent.name)
        return snapshot


def _refresh_thesis_validation(prior, snapshot: ResearchDeskSnapshot) -> ResearchDeskSnapshot:
    prior_symbols = {
        s.get("symbol", "") for s in prior.stocks if isinstance(s, dict) and s.get("symbol")
    }
    current_symbols = set(snapshot.discovered_symbols)
    validated = sorted(prior_symbols & current_symbols)
    invalidated = sorted(prior_symbols - current_symbols)
    overnight_news = len(snapshot.news_intelligence.articles)
    prior_regime = str(prior.market_regime.get("market_regime", ""))
    current_bias = snapshot.global_market.expected_india_opening_bias or "unknown"
    prior_thesis = (
        snapshot.thesis_validation.prior_thesis
        if snapshot.thesis_validation
        else (prior.executive_summary[:500] if prior.executive_summary else "")
    )
    validation = ThesisValidation(
        prior_date=prior.date.isoformat(),
        prior_thesis=prior_thesis,
        overnight_delta=(
            f"{overnight_news} overnight articles; prior regime {prior_regime}; "
            f"opening bias {current_bias}"
        ),
        validated_setups=validated,
        invalidated_setups=invalidated,
        thesis_intact=len(invalidated) <= len(validated),
    )
    return snapshot.model_copy(update={"thesis_validation": validation})
