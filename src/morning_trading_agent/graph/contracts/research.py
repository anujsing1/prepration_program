"""Research workflow contracts."""

from pydantic import BaseModel, Field

from morning_trading_agent.domain.entities.article import Article, SentimentAnalysis, Stock
from morning_trading_agent.domain.entities.beneficiary import ArticleStockMention
from morning_trading_agent.domain.entities.event import EventRecord
from morning_trading_agent.graph.contracts.metadata import WorkflowRunMetadata


class ResearchWorkflowState(BaseModel):
    """Input state for research workflow."""

    run_date: str
    dry_run: bool = False
    llm_provider: str = "stub"
    articles: list[Article] = Field(default_factory=list)


class ResearchWorkflowResult(BaseModel):
    """Output from research workflow."""

    identified_stocks: list[Stock] = Field(default_factory=list)
    stock_mentions: list[ArticleStockMention] = Field(default_factory=list)
    symbol_article_map: dict[str, list[str]] = Field(default_factory=dict)
    event_records: list[EventRecord] = Field(default_factory=list)
    sentiment_results: list[SentimentAnalysis] = Field(default_factory=list)
    classification_summary: dict[str, int] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    metadata: WorkflowRunMetadata = Field(default_factory=WorkflowRunMetadata)
