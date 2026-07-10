"""Markdown rendering for pipeline diagnostics reports."""

from __future__ import annotations

from morning_trading_agent.domain.value_objects.pipeline_diagnostics import (
    PipelineDiagnosticsReport,
)


class PipelineDiagnosticsReportBuilder:
    """Renders PipelineDiagnosticsReport to markdown."""

    def build(self, report: PipelineDiagnosticsReport) -> str:
        return report.to_markdown()
