"""Technical workflow contracts."""

from pydantic import BaseModel, Field

from morning_trading_agent.domain.entities.article import Stock
from morning_trading_agent.domain.entities.technical import TechnicalAnalysisResult
from morning_trading_agent.graph.contracts.metadata import WorkflowRunMetadata


class TechnicalWorkflowState(BaseModel):
    """Input state for technical workflow."""

    run_date: str
    dry_run: bool = False
    identified_stocks: list[Stock] = Field(default_factory=list)


class TechnicalWorkflowResult(BaseModel):
    """Output from technical workflow."""

    technical_results: list[TechnicalAnalysisResult] = Field(default_factory=list)
    failed_symbols: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    metadata: WorkflowRunMetadata = Field(default_factory=WorkflowRunMetadata)
