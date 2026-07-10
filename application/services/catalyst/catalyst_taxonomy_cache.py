"""Cached catalyst taxonomy for workflow runs."""

from __future__ import annotations

import structlog

from morning_trading_agent.domain.entities.catalyst_taxonomy import CatalystTaxonomyEntry
from morning_trading_agent.domain.repositories.catalyst_taxonomy_repository import (
    CatalystTaxonomyRepository,
)


class CatalystTaxonomyCache:
    """In-process cache of active catalyst taxonomy."""

    def __init__(self, repository: CatalystTaxonomyRepository, *, source: str = "db") -> None:
        self._repository = repository
        self._source = source
        self._logger = structlog.get_logger(self.__class__.__name__)
        self._entries: list[CatalystTaxonomyEntry] | None = None
        self._by_code: dict[str, CatalystTaxonomyEntry] = {}
        self._aliases: dict[str, str] = {}

    def set_aliases(self, aliases: dict[str, str]) -> None:
        self._aliases = {k.upper(): v.upper() for k, v in aliases.items()}

    async def load(self) -> list[CatalystTaxonomyEntry]:
        if self._entries is not None:
            return self._entries
        self._entries = await self._repository.get_all_active()
        self._by_code = {entry.catalyst_code.upper(): entry for entry in self._entries}
        self._logger.info("taxonomy_loaded", count=len(self._entries), source=self._source)
        return self._entries

    def invalidate(self) -> None:
        self._entries = None
        self._by_code = {}

    def get_by_code(self, code: str) -> CatalystTaxonomyEntry | None:
        normalized = code.upper()
        alias = self._aliases.get(normalized, normalized)
        return self._by_code.get(alias) or self._by_code.get(normalized)

    def is_weak(self, code: str) -> bool:
        entry = self.get_by_code(code)
        if entry is None:
            return False
        return entry.is_weak

    def codes(self) -> list[str]:
        return list(self._by_code.keys())
