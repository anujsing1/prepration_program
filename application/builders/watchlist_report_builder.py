"""Watchlist report builder using Builder pattern."""

from datetime import datetime

from morning_trading_agent.domain.entities.article import (
    DailyReport,
    TradingCandidate,
    Watchlist,
    WatchlistEntry,
)
from morning_trading_agent.domain.value_objects.sentiment import SentimentDirection
from morning_trading_agent.domain.value_objects.session_report_titles import (
    watchlist_report_title,
)
from morning_trading_agent.domain.value_objects.trading_session import TradingSessionMode


class WatchlistReportBuilder:
    """Builds watchlist entities and fallback markdown reports."""

    def build_watchlist(
        self,
        candidates: list[TradingCandidate],
        *,
        run_date: datetime,
        strategy: str,
        session_mode: TradingSessionMode | None = None,
    ) -> Watchlist:
        """Build a Watchlist from ranked candidates."""
        entries: list[WatchlistEntry] = []
        for rank, candidate in enumerate(candidates, start=1):
            explanation = candidate.explanation
            key_catalyst = (
                explanation.primary_catalyst
                if explanation
                else candidate.sentiment.primary_catalyst_summary or candidate.sentiment.reason[:200]
            )
            entries.append(
                WatchlistEntry(
                    rank=rank,
                    candidate=candidate,
                    risk_level=self._assess_risk(candidate),
                    key_catalyst=key_catalyst[:200],
                    notes=self._build_notes(candidate),
                    explanation=explanation,
                )
            )
        return Watchlist(
            run_date=run_date,
            strategy=strategy,
            session_mode=session_mode.value if session_mode else None,
            entries=entries,
        )

    def build_fallback_report(
        self,
        watchlist: Watchlist,
        candidates: list[TradingCandidate],
        *,
        session: TradingSessionMode | None = None,
        long_candidates: list[TradingCandidate] | None = None,
        short_candidates: list[TradingCandidate] | None = None,
        neutral_candidates: list[TradingCandidate] | None = None,
    ) -> DailyReport:
        """Build a deterministic markdown report without LLM."""
        long_pool = long_candidates or []
        short_pool = short_candidates or []
        neutral_pool = neutral_candidates or []
        use_directional = bool(long_pool or short_pool or neutral_pool)
        resolved_session = session
        if resolved_session is None and watchlist.session_mode:
            resolved_session = TradingSessionMode(watchlist.session_mode)
        title = watchlist_report_title(resolved_session or TradingSessionMode.PRE_MARKET)

        lines = [
            f"# {title} — {watchlist.run_date.strftime('%Y-%m-%d')}",
            f"**Strategy:** {watchlist.strategy}",
            "",
            "*Research watchlist for stocks to monitor at market open. Not trading advice.*",
            "",
        ]

        if use_directional:
            if long_pool:
                lines.extend(self._directional_entries("LONG Watchlist", long_pool))
            if short_pool:
                lines.extend(self._directional_entries("SHORT Opportunities", short_pool))
            if neutral_pool:
                lines.extend(self._directional_entries("NEUTRAL / Confirm", neutral_pool))
        else:
            for entry in watchlist.entries:
                lines.extend(self._entry_lines(entry))

        return DailyReport(
            run_date=watchlist.run_date,
            markdown="\n".join(lines),
            watchlist_id=watchlist.id,
            metadata={"strategy": watchlist.strategy, "count": len(candidates)},
        )

    def _directional_entries(
        self, title: str, pool: list[TradingCandidate]
    ) -> list[str]:
        lines = [f"## {title}", ""]
        for rank, candidate in enumerate(pool, start=1):
            lines.extend(self._candidate_detail_lines(candidate, rank))
        return lines

    def _entry_lines(self, entry: WatchlistEntry) -> list[str]:
        return self._candidate_detail_lines(entry.candidate, entry.rank, entry)

    def _candidate_detail_lines(
        self,
        candidate: TradingCandidate,
        rank: int,
        entry: WatchlistEntry | None = None,
    ) -> list[str]:
        c = candidate
        explanation = (entry.explanation if entry else None) or c.explanation
        key_catalyst = (
            entry.key_catalyst
            if entry
            else (
                explanation.primary_catalyst
                if explanation
                else c.sentiment.primary_catalyst_summary or c.sentiment.reason[:200]
            )
        )
        score = c.adjusted_score or c.final_score
        tier = c.watchlist_tier or "—"
        lines = [
            f"### #{rank} {c.stock.symbol}",
            f"**{c.stock.company_name}**",
            "",
            f"**Score:** {score:.0f} (final {c.final_score:.0f}, tier {tier})",
            "",
            "**Catalyst:**",
            explanation.primary_catalyst if explanation else key_catalyst,
            "",
        ]
        if explanation and explanation.catalyst_magnitude:
            lines.extend(
                [
                    f"**Magnitude:** {explanation.catalyst_magnitude}",
                    f"**Materiality:** {explanation.materiality_score:.0f}/100"
                    if explanation.materiality_score is not None
                    else "",
                    f"**Tradability:** {explanation.tradability_score:.0f}/100"
                    if explanation.tradability_score is not None
                    else "",
                    "",
                ]
            )
        lines.extend(
            [
                "**Technical Strength:**",
                explanation.technical_summary if explanation else self._build_notes(c),
                "",
                "**Sentiment:**",
                f"{c.sentiment.direction.value.title()} ({c.news_score:.0f}/100)",
                "",
                "**Freshness:**",
                explanation.freshness_summary if explanation else f"{c.freshness_score:.0f}/100",
                "",
                "**Risk:**",
                "; ".join(explanation.risk_factors)
                if explanation and explanation.risk_factors
                else (entry.risk_level if entry else self._assess_risk(c)),
                "",
                "**Reason:**",
                explanation.reason_for_ranking if explanation else c.sentiment.reason,
                "",
            ]
        )
        return lines

    @staticmethod
    def _assess_risk(candidate: TradingCandidate) -> str:
        if candidate.explanation and len(candidate.explanation.risk_factors) >= 2:
            return "High"
        if candidate.technical.atr > 0 and candidate.technical.relative_volume > 2.0:
            return "High"
        if candidate.sentiment.direction == SentimentDirection.BEARISH:
            return "High"
        if candidate.final_score >= 70:
            return "Low"
        return "Medium"

    @staticmethod
    def _build_notes(candidate: TradingCandidate) -> str:
        mode = candidate.selection_mode
        turnover = candidate.technical.avg_turnover_20d_inr
        liquidity = (
            f", Turnover20d: ₹{turnover / 1e7:.1f}Cr" if turnover > 0 else ""
        )
        return (
            f"RSI: {candidate.technical.rsi:.1f}, "
            f"RelVol: {candidate.technical.relative_volume:.2f}x, "
            f"Momentum: {candidate.technical.price_momentum:.1f}%"
            f"{liquidity}"
            f"{', Mode: ' + mode if mode != 'STRICT' else ''}"
        )
