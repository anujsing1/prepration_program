"""Build funnel loss report from debug stage summaries."""

from __future__ import annotations

from morning_trading_agent.domain.value_objects.pipeline_debug import (
    PipelineDebugReport,
    PipelineFunnelStep,
    PipelineStageSummary,
)
from morning_trading_agent.graph.state import TradingState


class PipelineFunnelReportBuilder:
    """Shows where candidates are lost between debug stages."""

    FUNNEL_STAGE_ORDER = (
        "fetch_news",
        "freshness_filter",
        "stock_extraction",
        "catalyst_classification",
        "technical_analysis",
        "candidate_creation",
        "score_validation",
        "ranking",
        "watchlist_selection",
    )

    LOSS_REASONS: dict[str, str] = {
        "fetch_news": "provider/freshness/dedup at fetch",
        "freshness_filter": "ingress quality gate",
        "stock_extraction": "no resolvable primary symbols",
        "catalyst_classification": "missing sentiment/analysis",
        "technical_analysis": "skipped — no sentiment join",
        "candidate_creation": "missing sentiment/technical join",
        "score_validation": "invalid or missing score fields",
        "ranking": "not ranked (empty pool)",
        "watchlist_selection": "adaptive filter / gate / tier cap",
    }

    def build(
        self,
        summaries: list[PipelineStageSummary],
        *,
        state: TradingState | None = None,
        null_findings=None,
        errors: list[str] | None = None,
    ) -> PipelineDebugReport:
        by_name = {summary.stage: summary for summary in summaries}
        funnel_steps: list[PipelineFunnelStep] = []
        prev_output: int | None = None

        for stage in self.FUNNEL_STAGE_ORDER:
            summary = by_name.get(stage)
            if summary is None:
                continue
            lost = 0
            if prev_output is not None:
                lost = max(0, prev_output - summary.output_count)
            funnel_steps.append(
                PipelineFunnelStep(
                    stage=stage,
                    count=summary.output_count,
                    lost=lost if prev_output is not None else summary.rejection_count,
                    loss_reason=self.LOSS_REASONS.get(stage, "stage_rejections"),
                )
            )
            prev_output = summary.output_count

        if state and funnel_steps:
            watchlist = state.get("watchlist")
            if watchlist and funnel_steps[-1].stage == "watchlist_selection":
                funnel_steps[-1].count = len(watchlist.entries)

        return PipelineDebugReport(
            stage_summaries=summaries,
            funnel_steps=funnel_steps,
            null_score_findings=null_findings or [],
            errors=errors or list(state.get("errors", [])) if state else [],
        )
