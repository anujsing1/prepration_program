"""Graph node protocol and logging decorator."""

import time
from typing import Protocol

import structlog

from morning_trading_agent.application.services.pipeline.pipeline_stage_registry import (
    measure_stage_counts,
)
from morning_trading_agent.graph.state import TradingState


class GraphNode(Protocol):
    """Protocol for class-based LangGraph nodes."""

    name: str

    async def execute(self, state: TradingState) -> TradingState:
        """Execute node logic and return updated state."""


class LoggedGraphNode:
    """Decorator wrapping a GraphNode with structured logging."""

    def __init__(self, node: GraphNode) -> None:
        self._node = node
        self.name = node.name
        self._logger = structlog.get_logger(f"node.{node.name}")

    async def execute(self, state: TradingState) -> TradingState:
        debug = bool(state.get("pipeline_debug"))
        run_id = state.get("run_id", "")
        if debug:
            before = measure_stage_counts(self._infer_stage(state), state)
            self._logger.info(
                "pipeline_node_input",
                run_id=run_id,
                node=self.name,
                stage=self._infer_stage(state),
                input_count=before.input_count,
                input_detail=before.input_detail,
            )
        self._logger.info(
            "pipeline_event",
            run_id=run_id,
            stage=self.name,
            result="start",
            reason="",
        )
        start = time.monotonic()
        try:
            result = await self._node.execute(state)
            duration = time.monotonic() - start
            self._logger.info(
                "pipeline_event",
                run_id=run_id,
                stage=self.name,
                result="pass",
                reason="",
                duration_seconds=round(duration, 3),
            )
            if debug:
                after = measure_stage_counts(self._infer_stage(result), result)
                self._logger.info(
                    "pipeline_node_output",
                    run_id=run_id,
                    node=self.name,
                    output_count=after.output_count,
                    rejection_count=after.rejection_count,
                    output_detail=after.output_detail,
                    rejection_detail=after.rejection_detail,
                )
            return result
        except Exception as exc:
            duration = time.monotonic() - start
            self._logger.error(
                "pipeline_event",
                run_id=run_id,
                stage=self.name,
                result="fail",
                reason=str(exc),
                duration_seconds=round(duration, 3),
            )
            state["errors"].append(f"{self.name}: {exc}")
            return state

    @staticmethod
    def _infer_stage(state: TradingState) -> str:
        """Best-effort stage name for debug counters when running outside debug runner."""
        if state.get("watchlist") is not None or state.get("filtered_candidates"):
            return "watchlist_selection"
        if state.get("ranked_candidates"):
            return "ranking"
        if state.get("all_candidates"):
            return "candidate_creation"
        if state.get("technical_results"):
            return "technical_analysis"
        if state.get("sentiment_results"):
            return "catalyst_classification"
        if state.get("identified_stocks"):
            return "stock_extraction"
        if state.get("rejected_articles"):
            return "freshness_filter"
        return "fetch_news"
