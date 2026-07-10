"""Admin use cases for catalyst taxonomy management."""

from __future__ import annotations

from uuid import UUID

from morning_trading_agent.domain.entities.catalyst_taxonomy import (
    CatalystTaxonomyEntry,
    PendingCatalystProposal,
    PendingCatalystStatus,
)
from morning_trading_agent.domain.repositories.catalyst_taxonomy_repository import (
    CatalystTaxonomyRepository,
)


class ManageCatalystTaxonomyUseCase:
    """Approve, reject, and list pending catalyst proposals."""

    def __init__(self, repository: CatalystTaxonomyRepository) -> None:
        self._repository = repository

    async def list_pending(
        self, *, status: PendingCatalystStatus | None = PendingCatalystStatus.PENDING
    ) -> list[PendingCatalystProposal]:
        return await self._repository.list_pending(status=status)

    async def approve(self, pending_id: UUID) -> CatalystTaxonomyEntry:
        return await self._repository.approve_pending(pending_id)

    async def reject(self, pending_id: UUID) -> PendingCatalystProposal:
        return await self._repository.reject_pending(pending_id)
