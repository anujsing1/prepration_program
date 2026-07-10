"""Base protocol for research desk agents."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from morning_trading_agent.domain.value_objects.agent_health import AgentExecutionError, AgentHealth

if TYPE_CHECKING:
    from morning_trading_agent.domain.value_objects.research_desk import ResearchDeskSnapshot


class ResearchDeskAgent(ABC):
    """Specialized agent that reads and updates a shared research desk snapshot."""

    name: str = "base"
    strict: bool = True

    @abstractmethod
    async def run(self, snapshot: ResearchDeskSnapshot) -> ResearchDeskSnapshot:
        """Execute agent logic and return updated snapshot."""

    def _attach_health(self, snapshot: ResearchDeskSnapshot, health: AgentHealth) -> ResearchDeskSnapshot:
        records = list(snapshot.metadata.get("agent_health", []))
        records.append(health.model_dump())
        return snapshot.model_copy(update={"metadata": {**snapshot.metadata, "agent_health": records}})

    def _finalize_health(
        self,
        snapshot: ResearchDeskSnapshot,
        health: AgentHealth,
        *,
        inputs: dict[str, object] | None = None,
        outputs: dict[str, object] | None = None,
    ) -> ResearchDeskSnapshot:
        health.executed = True
        observability = snapshot.metadata.get("_observability")
        if observability is not None:
            observability.record_agent(health, inputs=inputs, outputs=outputs)
        if self.strict:
            health.fail_if_no_real_data(strict=True)
        return self._attach_health(snapshot, health)
