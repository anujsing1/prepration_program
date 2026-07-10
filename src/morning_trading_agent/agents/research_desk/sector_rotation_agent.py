"""Sector Rotation Agent — NSE sector index relative strength."""

from __future__ import annotations

import structlog

from morning_trading_agent.agents.research_desk.base import ResearchDeskAgent
from morning_trading_agent.application.services.research_desk.research_market_data_service import (
    SECTOR_INDEX_NAMES,
    ResearchMarketDataService,
)
from morning_trading_agent.domain.value_objects.agent_health import AgentHealth
from morning_trading_agent.domain.value_objects.research_desk import (
    ResearchDeskSnapshot,
    SectorClassification,
    SectorRotationAnalysis,
    SectorRotationItem,
)


class SectorRotationAgent(ResearchDeskAgent):
    """Classify NSE sector indices as leading/improving/weakening/lagging."""

    name = "sector_rotation"

    def __init__(self, market_data: ResearchMarketDataService) -> None:
        self._market = market_data
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def run(self, snapshot: ResearchDeskSnapshot) -> ResearchDeskSnapshot:
        health = AgentHealth(agent=self.name, data_sources=["nse_allIndices"])
        indices, _breadth = await self._market.load_india_snapshot()
        if not indices:
            health.errors.append("NSE sector indices unavailable")
            return self._finalize_health(snapshot, health)

        items: list[SectorRotationItem] = []
        for sector, index_name in SECTOR_INDEX_NAMES.items():
            snap = self._market.index_for_label(indices, sector)
            if snap is None:
                health.warnings.append(f"No data for sector {sector} ({index_name})")
                continue
            items.append(
                SectorRotationItem(
                    sector=sector,
                    relative_strength=round(snap.change_pct, 2),
                    momentum_pct=round(snap.change_pct, 2),
                    volume_expansion=round(min(100.0, snap.volume / 1e9), 1) if snap.volume else 0.0,
                    institutional_participation=round(
                        min(100.0, snap.advance / max(snap.advance + snap.decline, 1) * 100), 1
                    ),
                    classification=SectorClassification.LAGGING,
                )
            )

        if len(items) < 3:
            health.errors.append(f"Only {len(items)} sectors loaded; minimum 3 required")
            health.used_real_data = False
            return self._finalize_health(snapshot, health)

        health.used_real_data = True
        health.records_processed = len(items)
        avg_momentum = sum(i.momentum_pct for i in items) / len(items)
        for i, item in enumerate(items):
            rel = item.momentum_pct - avg_momentum
            items[i] = item.model_copy(
                update={
                    "relative_strength": round(rel, 2),
                    "classification": _classify_rel(rel, item.momentum_pct),
                }
            )

        items.sort(key=lambda s: s.relative_strength, reverse=True)
        leaders = [s.sector for s in items if s.classification == SectorClassification.LEADING]
        laggards = [s.sector for s in items if s.classification == SectorClassification.LAGGING]
        if len(leaders) < 3:
            leaders = [s.sector for s in items[:3]]
        if len(laggards) < 3:
            laggards = [s.sector for s in reversed(items[-3:])]

        analysis = SectorRotationAnalysis(sectors=items, leaders=leaders[:3], laggards=laggards[:3])
        health.confidence = min(1.0, len(items) / len(SECTOR_INDEX_NAMES))
        self._logger.info("sector_rotation_complete", leaders=leaders, laggards=laggards)
        snapshot = snapshot.model_copy(update={"sector_rotation": analysis})
        return self._finalize_health(snapshot, health, outputs={"sectors": len(items), "leaders": leaders})


def _classify_rel(rel: float, momentum: float) -> SectorClassification:
    if rel > 0.5 and momentum > 0:
        return SectorClassification.LEADING
    if rel > 0:
        return SectorClassification.IMPROVING
    if rel < -0.5 and momentum < 0:
        return SectorClassification.LAGGING
    return SectorClassification.WEAKENING
