"""Workflow I/O contracts."""

from morning_trading_agent.graph.contracts.metadata import WorkflowRunMetadata
from morning_trading_agent.graph.contracts.news import NewsWorkflowResult, NewsWorkflowState
from morning_trading_agent.graph.contracts.ranking import RankingWorkflowResult, RankingWorkflowState
from morning_trading_agent.graph.contracts.reporting import (
    ReportingWorkflowResult,
    ReportingWorkflowState,
)
from morning_trading_agent.graph.contracts.research import (
    ResearchWorkflowResult,
    ResearchWorkflowState,
)
from morning_trading_agent.graph.contracts.technical import (
    TechnicalWorkflowResult,
    TechnicalWorkflowState,
)
from morning_trading_agent.graph.contracts.watchlist import (
    WatchlistWorkflowResult,
    WatchlistWorkflowState,
)

__all__ = [
    "WorkflowRunMetadata",
    "NewsWorkflowState",
    "NewsWorkflowResult",
    "ResearchWorkflowState",
    "ResearchWorkflowResult",
    "TechnicalWorkflowState",
    "TechnicalWorkflowResult",
    "RankingWorkflowState",
    "RankingWorkflowResult",
    "WatchlistWorkflowState",
    "WatchlistWorkflowResult",
    "ReportingWorkflowState",
    "ReportingWorkflowResult",
]
