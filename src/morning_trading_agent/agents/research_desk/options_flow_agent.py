"""Options Intelligence Agent — NSE option chain analytics."""

from __future__ import annotations

import structlog

from morning_trading_agent.agents.research_desk.base import ResearchDeskAgent
from morning_trading_agent.application.services.research_desk.research_market_data_service import (
    ResearchMarketDataService,
)
from morning_trading_agent.domain.value_objects.agent_health import AgentHealth
from morning_trading_agent.domain.value_objects.research_desk import OptionsFlowAnalysis, ResearchDeskSnapshot

_REJECTED = frozenset({"neutral", "mixed", "none"})


class OptionsFlowAgent(ResearchDeskAgent):
    """Real NSE option chain PCR, max pain, OI support/resistance."""

    name = "options_flow"
    strict = True

    def __init__(self, market_data: ResearchMarketDataService) -> None:
        self._market = market_data
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def run(self, snapshot: ResearchDeskSnapshot) -> ResearchDeskSnapshot:
        health = AgentHealth(agent=self.name, data_sources=["nse_option_chain_indices"])
        chain = await self._market.load_option_chain("NIFTY")
        if chain is None or chain.pcr <= 0 or chain.max_pain <= 0:
            health.errors.append("NSE NIFTY option chain unavailable or incomplete")
            return self._finalize_health(snapshot, health)

        if not chain.support or not chain.resistance:
            health.errors.append("OI support/resistance levels could not be computed")
            return self._finalize_health(snapshot, health)

        vol = (
            "elevated"
            if snapshot.market_structure.volatility_regime == "elevated"
            else "compressed"
            if snapshot.market_structure.volatility_regime == "compressed"
            else "normal"
        )
        if vol.lower() in _REJECTED:
            vol = "normal"

        analysis = OptionsFlowAnalysis(
            pcr=chain.pcr,
            max_pain=chain.max_pain,
            support=chain.support,
            resistance=chain.resistance,
            expected_range={"low": chain.range_low, "high": chain.range_high, "spot": chain.spot},
            volatility=vol,
            confidence=round(chain.confidence, 2),
            call_writing_strikes=chain.call_writing_strikes,
            put_writing_strikes=chain.put_writing_strikes,
            oi_buildup=chain.oi_buildup,
            gamma_risk=chain.gamma_risk,
            data_availability="nse_option_chain",
        )
        health.used_real_data = True
        health.records_processed = int(chain.call_oi_total + chain.put_oi_total)
        health.confidence = analysis.confidence
        self._logger.info(
            "options_flow_complete",
            pcr=chain.pcr,
            max_pain=chain.max_pain,
            support=chain.support,
            resistance=chain.resistance,
        )
        snapshot = snapshot.model_copy(update={"options_flow": analysis})
        return self._finalize_health(
            snapshot,
            health,
            outputs={
                "pcr": chain.pcr,
                "max_pain": chain.max_pain,
                "support": chain.support,
                "resistance": chain.resistance,
            },
        )
