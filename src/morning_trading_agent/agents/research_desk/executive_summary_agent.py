"""Executive Summary Agent — institutional research desk report."""

from __future__ import annotations

import structlog

from morning_trading_agent.agents.research_desk.base import ResearchDeskAgent
from morning_trading_agent.domain.value_objects.research_desk import ResearchDeskSnapshot


class ExecutiveSummaryAgent(ResearchDeskAgent):
    """Synthesize all agent outputs into an executive research report."""

    name = "executive_summary"
    strict = False

    def __init__(self) -> None:
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def run(self, snapshot: ResearchDeskSnapshot) -> ResearchDeskSnapshot:
        from morning_trading_agent.domain.value_objects.agent_health import AgentHealth

        health = AgentHealth(agent=self.name, data_sources=["research_desk_snapshot"])
        lines = [
            f"# Institutional Research Desk — {snapshot.session_date.isoformat()}",
            f"**Mode:** {snapshot.mode.value}",
            "",
            "## Market Summary",
            _market_section(snapshot),
            "",
            "## Global Summary",
            _global_section(snapshot),
            "",
            "## Institutional Summary",
            _institutional_section(snapshot),
            "",
            "## Sector Rotation",
            _sector_section(snapshot),
            "",
            "## Major Events",
            _events_section(snapshot),
            "",
            "## Options Analysis",
            _options_section(snapshot),
            "",
            "## Historical Analogues",
            snapshot.historical_context.narrative,
            "",
            "## Long Candidates",
            _candidates_section(snapshot.portfolio.long_watchlist),
            "",
            "## Short Candidates",
            _candidates_section(snapshot.portfolio.short_watchlist),
            "",
            "## Risk Assessment",
            _risk_section(snapshot),
            "",
            "## Tomorrow's Market Thesis",
            _thesis_section(snapshot),
        ]
        if snapshot.thesis_validation:
            lines.extend(
                [
                    "",
                    "## Thesis Validation (Premarket)",
                    f"- Prior thesis intact: **{snapshot.thesis_validation.thesis_intact}**",
                    f"- Validated setups: {', '.join(snapshot.thesis_validation.validated_setups) or 'none'}",
                    f"- Invalidated setups: {', '.join(snapshot.thesis_validation.invalidated_setups) or 'none'}",
                    f"- Overnight delta: {snapshot.thesis_validation.overnight_delta}",
                ]
            )

        health_rows = snapshot.metadata.get("agent_health", [])
        if health_rows:
            lines.extend(["", "## Agent Health"])
            for row in health_rows:
                if isinstance(row, dict):
                    lines.append(
                        f"- **{row.get('agent')}**: real_data={row.get('used_real_data')} "
                        f"confidence={row.get('confidence')} records={row.get('records_processed')} "
                        f"errors={len(row.get('errors', []))}"
                    )

        report = "\n".join(lines)
        self._logger.info("executive_summary_complete", chars=len(report))
        snapshot = snapshot.model_copy(update={"executive_summary": report})
        health.used_real_data = True
        health.records_processed = 1
        health.confidence = 1.0
        return self._finalize_health(snapshot, health, outputs={"report_chars": len(report)})


def _market_section(snapshot: ResearchDeskSnapshot) -> str:
    ms = snapshot.market_structure
    mr = snapshot.market_regime
    return (
        f"- Structure regime: **{ms.market_regime}** | Trend: **{ms.trend}**\n"
        f"- Institutional regime: **{mr.regime}** (bull {mr.bullish_probability:.0%} / bear {mr.bearish_probability:.0%})\n"
        f"- Breadth: {ms.breadth_score}/100 | Risk: {ms.risk_score}/100\n"
        f"- Continuation probability: {ms.continuation_probability:.0%}\n"
        f"- Volatility: {ms.volatility_regime}"
    )


def _global_section(snapshot: ResearchDeskSnapshot) -> str:
    gm = snapshot.global_market
    return (
        f"- Global risk score: {gm.global_risk_score}/100\n"
        f"- Overnight sentiment: **{gm.overnight_sentiment}**\n"
        f"- Expected India open: **{gm.expected_india_opening_bias}**"
    )


def _institutional_section(snapshot: ResearchDeskSnapshot) -> str:
    inst = snapshot.institutional_flow
    return (
        f"- Smart money: **{inst.smart_money_direction}**\n"
        f"- Confidence: {inst.institutional_confidence_score}/100\n"
        f"- OI signal: {inst.open_interest_signal}"
    )


def _sector_section(snapshot: ResearchDeskSnapshot) -> str:
    sr = snapshot.sector_rotation
    lines = [f"- Top 3 Leaders: {', '.join(sr.leaders[:3])}", f"- Top 3 Laggards: {', '.join(sr.laggards[:3])}"]
    for item in sr.sectors[:3]:
        lines.append(
            f"  - {item.sector}: RS {item.relative_strength:.2f} | momentum {item.momentum_pct:.2f}% "
            f"| vol expansion {item.volume_expansion:.1f} | inst participation {item.institutional_participation:.1f}"
        )
    return "\n".join(lines)


def _events_section(snapshot: ResearchDeskSnapshot) -> str:
    if not snapshot.corporate_events.events:
        return "- No major corporate events identified."
    return "\n".join(
        f"- **{e.symbol}** [{e.event_subtype}] impact {e.impact_score:.0f} "
        f"duration {e.duration} conf {e.confidence_score:.0%}: {e.title[:70]}"
        for e in snapshot.corporate_events.events[:8]
    )


def _options_section(snapshot: ResearchDeskSnapshot) -> str:
    opt = snapshot.options_flow
    er = opt.expected_range
    low = er.get("low", 0)
    high = er.get("high", 0)
    return (
        f"- Support: {opt.support} | Resistance: {opt.resistance}\n"
        f"- Max pain: {opt.max_pain} | PCR: {opt.pcr}\n"
        f"- Expected range: {low} – {high} | Volatility: {opt.volatility}\n"
        f"- OI buildup: {opt.oi_buildup} | Gamma risk: {opt.gamma_risk} | Confidence: {opt.confidence:.0%}"
    )


def _candidates_section(candidates) -> str:
    if not candidates:
        return "- None"
    return "\n".join(
        f"- **{c.symbol}** ({c.sector}, {c.direction}) — score {c.score:.1f} "
        f"entry {c.entry} SL {c.stoploss} TP {c.target} RR {c.risk_reward:.1f} "
        f"[conf {c.confidence:.0%}]: {c.thesis[:60]}"
        for c in candidates[:10]
    )


def _risk_section(snapshot: ResearchDeskSnapshot) -> str:
    risk = snapshot.risk
    notes = "\n".join(f"  - {n}" for n in risk.risk_reward_notes)
    return (
        f"- Max exposure: {risk.max_portfolio_exposure_pct}%\n"
        f"- Position size: {risk.recommended_position_size_pct}% per idea\n"
        f"- Est. VaR: {risk.portfolio_var_pct}% | Drawdown: {risk.expected_drawdown_pct}%\n"
        f"{notes}"
    )


def _thesis_section(snapshot: ResearchDeskSnapshot) -> str:
    ms = snapshot.market_structure
    gm = snapshot.global_market
    longs = ", ".join(c.symbol for c in snapshot.portfolio.long_watchlist[:5]) or "none"
    return (
        f"India is in a **{ms.market_regime}** regime with **{gm.expected_india_opening_bias}** "
        f"opening bias. Institutional flow suggests **{snapshot.institutional_flow.smart_money_direction}**. "
        f"Focus long ideas: {longs}. "
        f"Historical analogue confidence: {snapshot.historical_context.confidence_score:.0%}."
    )
