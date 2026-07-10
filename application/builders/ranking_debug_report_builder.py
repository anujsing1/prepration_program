"""Human-readable ranking pipeline debug report."""

from morning_trading_agent.application.builders.catalyst_diagnostics_report_builder import (
    CatalystDiagnosticsReportBuilder,
)
from morning_trading_agent.application.builders.classification_summary_builder import (
    ClassificationSummaryBuilder,
)
from morning_trading_agent.application.builders.weighted_contribution_report_builder import (
    WeightedContributionReportBuilder,
)
from morning_trading_agent.application.services.pipeline.tradability_resolver import (
    canonical_tradability_score,
)
from morning_trading_agent.config.premarket_config import RankingWeightV2Config
from morning_trading_agent.domain.entities.pipeline_trace import CandidatePipelineTrace
from morning_trading_agent.graph.state import TradingState


class RankingDebugReportBuilder:
    """Formats accepted, rejected, near-miss candidates with weighted contributions."""

    def __init__(
        self,
        *,
        weight_config: RankingWeightV2Config | None = None,
        weighted_builder: WeightedContributionReportBuilder | None = None,
        classification_builder: ClassificationSummaryBuilder | None = None,
    ) -> None:
        self._weighted = weighted_builder or WeightedContributionReportBuilder(
            weight_config=weight_config
        )
        self._classification = classification_builder or ClassificationSummaryBuilder()
        self._catalyst_diagnostics = CatalystDiagnosticsReportBuilder()

    def build(self, state: TradingState) -> str:
        lines = [
            "# Ranking Pipeline Debug Report",
            "",
            f"**Extracted:** {len(state.get('identified_stocks', []))}",
            f"**Built:** {len(state.get('all_candidates', []))}",
            f"**Dropped (missing analysis):** {state.get('dropped_missing_analysis_count', 0)}",
            f"**Survived filtering:** {len(state.get('filtered_candidates', []))}",
            f"**Rejected:** {len(state.get('rejected_candidates', []))}",
            f"**Near miss:** {len(state.get('near_miss_candidates', []))}",
            f"**Final watchlist:** {len(state.get('ranked_candidates', []))}",
            f"**LONG / SHORT / NEUTRAL:** "
            f"{len(state.get('long_candidates', []))} / "
            f"{len(state.get('short_candidates', []))} / "
            f"{len(state.get('neutral_candidates', []))}",
            "",
            "## Funnel Metrics",
            f"- Articles fetched: {len(state.get('articles', [])) + len(state.get('rejected_articles', []))}",
            f"- Stocks extracted: {len(state.get('identified_stocks', []))}",
            f"- Classified: {state.get('classified_count', len(state.get('sentiment_results', [])))}",
            f"- Tradable catalysts: {state.get('tradable_catalyst_count', 0)}",
            f"- Non-tradable catalysts: {state.get('non_tradable_catalyst_count', 0)}",
            f"- Candidates created: {len(state.get('all_candidates', []))}",
            f"- Candidates rejected (tradability): {state.get('non_tradable_catalyst_count', 0)}",
            f"- Dropped (tradability): {state.get('dropped_tradability_count', 0)}",
            f"- Skipped technical analysis: {state.get('skipped_technical_count', 0)}",
            f"- Passed technical filters: {state.get('passed_technical_filters', len(state.get('filtered_candidates', [])))}",
            f"- Ranked: {len(state.get('sorted_candidates', state.get('ranked_candidates', [])))}",
            f"- Final watchlist size: {len(state.get('ranked_candidates', []))}",
            "",
        ]

        catalyst_sections = self._catalyst_diagnostics.build_sections(state)
        if catalyst_sections:
            lines.extend(catalyst_sections.splitlines())
            lines.append("")

        select_drops = state.get("select_drop_counts", {})
        if select_drops:
            lines.append("## Dropped at watchlist selection")
            for reason, count in sorted(select_drops.items()):
                lines.append(f"- {reason}: {count}")
            lines.append("")

        select_dropped_traces = [
            t
            for t in state.get("pipeline_traces", [])
            if t.stage == "select_dropped"
        ]
        if select_dropped_traces:
            lines.append("## Select-stage drop detail")
            for trace in sorted(select_dropped_traces, key=lambda t: t.symbol):
                lines.append(
                    f"- **{trace.symbol}**: score={trace.adjusted_score or trace.final_score:.0f}, "
                    f"tier={trace.watchlist_tier or '—'}, "
                    f"direction={trace.direction_bucket or trace.sentiment_direction or '—'}, "
                    f"reason={trace.select_drop_reason or trace.rejection_reason}"
                )
            lines.append("")

        rejection_counts = state.get("filter_rejection_counts", {})
        if rejection_counts:
            lines.append("## Rejection Breakdown")
            for reason, count in sorted(rejection_counts.items()):
                lines.append(f"- {reason}: {count}")
            lines.append("")

        classification = self._classification.from_state(state)
        if classification:
            lines.append("## Classification Summary")
            for catalyst_type, count in classification.items():
                lines.append(f"- {catalyst_type}: {count}")
            lines.append("")

        ranked = state.get("ranked_candidates", [])
        if ranked:
            lines.append("## Accepted Candidates")
            for candidate in ranked:
                lines.extend(self._weighted.format_candidate(candidate))
                lines.append("")

        rejected = state.get("rejected_candidates", [])
        tradability_rejections = state.get("tradability_rejections", [])
        reason_map = {
            t.symbol: t.rejection_reason
            for t in state.get("pipeline_traces", [])
            if t.rejected and t.rejection_reason
        }
        if tradability_rejections or rejected:
            lines.append("## Rejected Candidates")
            seen_symbols: set[str] = set()
            for detail in tradability_rejections:
                lines.append(detail.format_line())
                seen_symbols.add(detail.symbol)
            for candidate in rejected:
                symbol = candidate.stock.symbol
                if symbol in seen_symbols:
                    continue
                profile = candidate.sentiment.catalyst_tradability
                tradability = canonical_tradability_score(candidate.sentiment)
                if tradability is None and profile:
                    tradability = profile.tradability_score
                tradability = tradability or 0.0
                catalyst = candidate.sentiment.primary_catalyst_type.value
                reason = reason_map.get(symbol, profile.rejection_reason if profile else "filtered")
                lines.append(
                    f"{symbol} | {catalyst} | "
                    f"Tradability: {tradability:.0f}/100 | Reason: {reason}"
                )
            lines.append("")

        near_miss = state.get("near_miss_candidates", [])
        if near_miss:
            lines.append("## Near Miss Candidates")
            for candidate in near_miss:
                symbol = candidate.stock.symbol
                reason = reason_map.get(symbol, "filtered")
                quality = candidate.sentiment.catalyst_quality
                effective = candidate.effective_catalyst_score or candidate.catalyst_score
                lines.append(f"### {symbol}")
                lines.append(f"Rejected: {reason}")
                lines.append("Near Miss: YES")
                lines.append(f"Catalyst: {effective:.0f}")
                if quality:
                    lines.append(f"Materiality: {quality.materiality_score:.0f}")
                    lines.append(f"Tradability: {quality.tradability_score:.0f}")
                if candidate.sentiment.thematic_sector_catalyst:
                    lines.append(
                        "Note: Thematic defence/government procurement exposure"
                    )
                lines.append("")

        if state.get("debug_ranking"):
            traces = self._sorted_traces(state)
            if traces:
                lines.append("## Pipeline Traces (collapsed)")
                for trace in traces[:20]:
                    lines.extend(self._format_trace(trace))
                    lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _sorted_traces(state: TradingState) -> list[CandidatePipelineTrace]:
        return sorted(
            state.get("pipeline_traces", []),
            key=lambda t: (t.rejected, -(t.final_score or 0), t.symbol),
        )

    @staticmethod
    def _format_trace(trace: CandidatePipelineTrace) -> list[str]:
        catalyst = trace.catalyst_type.value if trace.catalyst_type else "n/a"
        status = "REJECTED" if trace.rejected else "ACCEPTED"
        block = [
            f"### {trace.symbol} [{status}]",
            f"- catalyst: {catalyst} (score={trace.catalyst_score})",
            f"- final_score: {trace.final_score}",
        ]
        if trace.rejection_reason:
            block.append(f"- rejection_reason: {trace.rejection_reason}")
        return block
