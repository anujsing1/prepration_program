"""Risk Management Agent — exposure, VaR, gap risk from live market state."""

from __future__ import annotations

import structlog

from morning_trading_agent.agents.research_desk.base import ResearchDeskAgent
from morning_trading_agent.domain.value_objects.agent_health import AgentHealth
from morning_trading_agent.domain.value_objects.research_desk import ResearchDeskSnapshot, RiskAssessment


class RiskManagementAgent(ResearchDeskAgent):
    """Portfolio risk controls derived from market structure and positions."""

    name = "risk_management"

    def __init__(self, *, base_position_pct: float = 2.0) -> None:
        self._base_position = base_position_pct
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def run(self, snapshot: ResearchDeskSnapshot) -> ResearchDeskSnapshot:
        health = AgentHealth(agent=self.name, data_sources=["market_structure", "global_market", "portfolio"])
        risk_score = snapshot.market_structure.risk_score
        vix = float(snapshot.market_structure.indices.get("INDIA_VIX", {}).get("close", 0.0) or 0.0)
        long_count = len(snapshot.portfolio.long_watchlist)
        symbols = [c.symbol for c in snapshot.portfolio.long_watchlist]
        unique_sectors = {
            next(
                (s.sector for s in snapshot.sector_rotation.sectors if c.symbol in s.sector),
                "unknown",
            )
            for c in snapshot.portfolio.long_watchlist
        }

        exposure = min(100.0, long_count * self._base_position)
        position_size = self._base_position
        if risk_score > 65 or vix > 20:
            position_size = max(0.5, self._base_position * 0.5)
            exposure = min(exposure, 6.0)
        elif risk_score < 40 and vix < 15:
            position_size = min(3.0, self._base_position * 1.2)

        gap_risk_note = ""
        if snapshot.global_market.overnight_sentiment == "risk_off":
            gap_risk_note = "Elevated overnight gap-down risk from global risk-off."
            exposure = min(exposure, max(4.0, exposure * 0.7))

        var_pct = round((risk_score / 100.0) * (vix / 15.0 if vix else 1.0) * 12.0, 2)
        drawdown = round(risk_score * 0.18 + vix * 0.3, 2)
        corr_warning = ""
        if len(symbols) != len(set(symbols)):
            corr_warning = "Duplicate symbols in watchlist."
        elif len(unique_sectors) < max(1, long_count // 2) and long_count >= 3:
            corr_warning = "High sector concentration in watchlist."

        notes = [
            f"Market risk {risk_score:.1f}/100, VIX {vix:.1f} → {position_size:.1f}% per position.",
            f"Max gross long exposure {exposure:.1f}%.",
        ]
        if gap_risk_note:
            notes.append(gap_risk_note)
        if snapshot.options_flow.support and snapshot.options_flow.resistance:
            notes.append(
                f"NIFTY OI range {snapshot.options_flow.support}–{snapshot.options_flow.resistance}."
            )

        assessment = RiskAssessment(
            max_portfolio_exposure_pct=round(exposure, 1),
            recommended_position_size_pct=round(position_size, 2),
            portfolio_var_pct=var_pct,
            expected_drawdown_pct=drawdown,
            correlation_warning=corr_warning,
            risk_reward_notes=notes,
        )
        health.used_real_data = True
        health.records_processed = long_count
        health.confidence = 0.8 if vix > 0 else 0.5
        self._logger.info("risk_management_complete", exposure=exposure, var=var_pct)
        snapshot = snapshot.model_copy(update={"risk": assessment})
        return self._finalize_health(snapshot, health, outputs={"exposure": exposure, "var": var_pct})
