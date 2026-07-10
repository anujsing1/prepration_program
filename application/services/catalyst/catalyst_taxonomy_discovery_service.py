"""Taxonomy-aware catalyst discovery and pending proposal handling."""

from __future__ import annotations

import structlog

from morning_trading_agent.application.services.catalyst.catalyst_taxonomy_cache import (
    CatalystTaxonomyCache,
)
from morning_trading_agent.domain.entities.catalyst_taxonomy import (
    CatalystClassificationOutcome,
    PendingCatalystProposal,
    PendingCatalystSummary,
)
from morning_trading_agent.domain.repositories.catalyst_taxonomy_repository import (
    CatalystTaxonomyRepository,
)
from morning_trading_agent.domain.value_objects.catalyst_codes import OTHER

_LOW_CONFIDENCE_THRESHOLD = 0.5
_SIMILARITY_THRESHOLD = 0.85


class CatalystTaxonomyDiscoveryService:
    """Handles DB-driven catalyst matching and pending discovery."""

    def __init__(
        self,
        *,
        repository: CatalystTaxonomyRepository,
        cache: CatalystTaxonomyCache,
        low_confidence_threshold: float = _LOW_CONFIDENCE_THRESHOLD,
    ) -> None:
        self._repository = repository
        self._cache = cache
        self._low_confidence = low_confidence_threshold
        self._logger = structlog.get_logger(self.__class__.__name__)
        self._run_discoveries: list[PendingCatalystSummary] = []

    @property
    def run_discoveries(self) -> list[PendingCatalystSummary]:
        return list(self._run_discoveries)

    def reset_run_discoveries(self) -> None:
        self._run_discoveries = []

    async def resolve(
        self,
        *,
        matched_existing: bool,
        catalyst_code: str | None,
        proposed_code: str | None,
        proposed_name: str | None,
        parent_category: str | None,
        description: str | None,
        confidence: float,
        reason: str,
        symbol: str,
        example_headline: str | None = None,
    ) -> CatalystClassificationOutcome:
        await self._cache.load()

        for raw_code in (catalyst_code, proposed_code):
            if not raw_code:
                continue
            normalized = raw_code.upper()
            entry = self._cache.get_by_code(normalized)
            if entry is not None:
                self._logger.info(
                    "catalyst_matched",
                    code=normalized,
                    confidence=confidence,
                    symbol=symbol,
                    match_type="exact_cache",
                )
                return CatalystClassificationOutcome(
                    catalyst_code=normalized,
                    matched_existing=True,
                    confidence=confidence,
                    reason=reason,
                )

        if matched_existing and catalyst_code:
            normalized = catalyst_code.upper()
            entry = self._cache.get_by_code(normalized)
            if entry is not None:
                self._logger.info(
                    "catalyst_matched",
                    code=normalized,
                    confidence=confidence,
                    symbol=symbol,
                )
                return CatalystClassificationOutcome(
                    catalyst_code=normalized,
                    matched_existing=True,
                    confidence=confidence,
                    reason=reason,
                )

        code = (proposed_code or catalyst_code or OTHER).upper()
        name = proposed_name or code.replace("_", " ").title()
        if matched_existing and self._cache.get_by_code(code):
            self._logger.info(
                "catalyst_matched",
                code=code,
                confidence=confidence,
                symbol=symbol,
            )
            return CatalystClassificationOutcome(
                catalyst_code=code,
                matched_existing=True,
                confidence=confidence,
                reason=reason,
            )

        if confidence >= self._low_confidence and matched_existing and catalyst_code:
            normalized = catalyst_code.upper()
            if self._cache.get_by_code(normalized):
                return CatalystClassificationOutcome(
                    catalyst_code=normalized,
                    matched_existing=True,
                    confidence=confidence,
                    reason=reason,
                )

        self._logger.info(
            "catalyst_proposed",
            proposed_code=code,
            confidence=confidence,
            symbol=symbol,
        )

        similar = await self._repository.find_similar(code, threshold=_SIMILARITY_THRESHOLD)
        if similar:
            match_code, score, source = similar[0]
            self._logger.info(
                "pending_catalyst_duplicate",
                existing_id=match_code,
                proposed_code=code,
                similarity=score,
                source=source,
            )
            if source == "active":
                return CatalystClassificationOutcome(
                    catalyst_code=match_code,
                    matched_existing=True,
                    confidence=confidence,
                    reason=f"semantic_match:{score:.2f}",
                )
            if source == "pending":
                existing = await self._repository.get_pending_by_code(match_code)
                if existing and existing.id:
                    updated = await self._repository.increment_pending(
                        existing.id,
                        example_headline=example_headline,
                        confidence=confidence,
                    )
                    self._record_discovery(updated, example_headline)
                    return CatalystClassificationOutcome(
                        catalyst_code=OTHER,
                        matched_existing=False,
                        confidence=confidence,
                        reason=reason,
                        proposed=updated,
                    )

        proposal = PendingCatalystProposal(
            proposed_code=code,
            proposed_name=name,
            parent_category=parent_category,
            description=description,
            example_headline=example_headline,
            confidence=confidence,
        )
        created = await self._repository.create_pending(proposal)
        await self._ensure_active_taxonomy(
            code=code,
            name=name,
            parent_category=parent_category,
            description=description,
        )
        self._logger.info(
            "pending_catalyst_created",
            id=str(created.id),
            proposed_code=created.proposed_code,
        )
        self._record_discovery(created, example_headline)
        return CatalystClassificationOutcome(
            catalyst_code=code,
            matched_existing=False,
            confidence=confidence,
            reason=reason,
            proposed=created,
        )

    async def _ensure_active_taxonomy(
        self,
        *,
        code: str,
        name: str,
        parent_category: str | None,
        description: str | None,
    ) -> None:
        normalized = code.upper()
        if self._cache.get_by_code(normalized) is not None:
            return
        from morning_trading_agent.domain.entities.catalyst_taxonomy import CatalystTaxonomyEntry

        entry = CatalystTaxonomyEntry(
            catalyst_code=normalized,
            catalyst_name=name,
            parent_category=parent_category,
            description=description,
            bullish_weight=50.0,
            bearish_weight=50.0,
            tradability_weight=45.0,
            is_active=True,
        )
        created = await self._repository.create_active(entry)
        await self._cache.load()
        self._logger.info(
            "catalyst_type_auto_registered",
            code=created.catalyst_code,
        )

    def _record_discovery(
        self, proposal: PendingCatalystProposal, example_headline: str | None
    ) -> None:
        summary = PendingCatalystSummary(
            proposed_code=proposal.proposed_code,
            occurrence_count=proposal.occurrence_count,
            confidence=proposal.confidence,
            example_headline=example_headline or proposal.example_headline or "",
        )
        for idx, existing in enumerate(self._run_discoveries):
            if existing.proposed_code == summary.proposed_code:
                self._run_discoveries[idx] = summary
                return
        self._run_discoveries.append(summary)
