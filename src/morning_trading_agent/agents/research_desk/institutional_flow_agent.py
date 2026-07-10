"""Institutional Flow Agent — FII/DII cash flows from NSE."""

from __future__ import annotations

import structlog

from morning_trading_agent.agents.research_desk.base import ResearchDeskAgent
from morning_trading_agent.application.services.research_desk.research_market_data_service import (
    ResearchMarketDataService,
)
from morning_trading_agent.domain.value_objects.agent_health import AgentHealth
from morning_trading_agent.domain.value_objects.research_desk import InstitutionalFlowAnalysis, ResearchDeskSnapshot


class InstitutionalFlowAgent(ResearchDeskAgent):
    """Analyze FII/DII net flows and derive institutional sentiment."""

    name = "institutional_flow"

    def __init__(self, market_data: ResearchMarketDataService) -> None:
        self._market = market_data
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def run(self, snapshot: ResearchDeskSnapshot) -> ResearchDeskSnapshot:
        health = AgentHealth(agent=self.name, data_sources=["nse_fiidiiTradeReact"])
        flow = await self._market.load_fii_dii()
        if flow is None:
            health.errors.append("FII/DII data unavailable from NSE")
            return self._finalize_health(snapshot, health)

        health.used_real_data = True
        health.records_processed = 2
        combined_net = flow.fii_net + flow.dii_net
        if flow.fii_net > 500 and flow.dii_net > 0:
            direction = "accumulation"
            confidence = min(95.0, 60.0 + abs(flow.fii_net) / 100.0)
            oi_signal = "long_buildup"
        elif flow.fii_net < -500 and flow.dii_net < 0:
            direction = "distribution"
            confidence = min(95.0, 60.0 + abs(flow.fii_net) / 100.0)
            oi_signal = "short_buildup"
        elif flow.fii_net > 0 and flow.dii_net < 0:
            direction = "fii_accumulation_dii_profit_booking"
            confidence = 65.0
            oi_signal = "mixed"
        elif flow.fii_net < 0 and flow.dii_net > 0:
            direction = "dii_support_fii_selling"
            confidence = 62.0
            oi_signal = "short_covering"
        else:
            direction = "balanced"
            confidence = 52.0 + min(10.0, abs(combined_net) / 200.0)
            oi_signal = "neutral"

        index_bias = "bullish" if combined_net > 0 else "bearish" if combined_net < -200 else "neutral"
        analysis = InstitutionalFlowAnalysis(
            smart_money_direction=direction,
            institutional_confidence_score=round(confidence, 1),
            fii_net=flow.fii_net,
            dii_net=flow.dii_net,
            index_futures_bias=index_bias,
            stock_futures_bias=direction,
            open_interest_signal=oi_signal,
            data_availability="nse_fii_dii",
        )
        health.confidence = 0.85
        self._logger.info(
            "institutional_flow_complete",
            direction=direction,
            fii_net=flow.fii_net,
            dii_net=flow.dii_net,
        )
        snapshot = snapshot.model_copy(update={"institutional_flow": analysis})
        return self._finalize_health(
            snapshot,
            health,
            outputs={"fii_net": flow.fii_net, "dii_net": flow.dii_net, "direction": direction},
        )
