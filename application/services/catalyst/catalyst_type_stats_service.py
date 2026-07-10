"""Evidence store for catalyst type statistics."""

from __future__ import annotations

import structlog

from morning_trading_agent.domain.entities.catalyst_type_stats import CatalystTypeStats
from morning_trading_agent.domain.repositories.catalyst_type_stats_repository import (
    CatalystTypeStatsRepository,
)


class CatalystTypeStatsService:
    """Records classification sightings and watchlist outcomes per catalyst code."""

    def __init__(self, repository: CatalystTypeStatsRepository) -> None:
        self._repository = repository
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def record_classification(self, code: str) -> CatalystTypeStats:
        normalized = code.upper()
        stats = await self._repository.upsert_classification(normalized)
        self._logger.debug(
            "catalyst_type_stats_classification",
            code=normalized,
            occurrence_count=stats.occurrence_count,
        )
        return stats

    async def record_outcome(
        self,
        code: str,
        *,
        accepted: bool,
        composite_score: float,
        tradability: float,
    ) -> CatalystTypeStats:
        normalized = code.upper()
        stats = await self._repository.record_outcome(
            normalized,
            accepted=accepted,
            composite_score=composite_score,
            tradability=tradability,
        )
        self._logger.debug(
            "catalyst_type_stats_outcome",
            code=normalized,
            accepted=accepted,
            average_score=stats.average_score,
        )
        return stats

    async def get_stats(self, code: str) -> CatalystTypeStats | None:
        return await self._repository.get_by_code(code.upper())

    async def list_all(self) -> list[CatalystTypeStats]:
        return await self._repository.list_all()
