"""Application layer ports (interfaces for external dependencies)."""

from abc import ABC, abstractmethod
from datetime import datetime

from morning_trading_agent.domain.entities.article import (
    Article,
    DailyReport,
    ExtractedStock,
    PriceSeries,
    SentimentAnalysis,
    Stock,
    TechnicalAnalysis,
    TradingCandidate,
    VolumeSeries,
    Watchlist,
)


class NewsProvider(ABC):
    """Port for fetching financial news."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier."""

    @abstractmethod
    async def fetch_news(self, *, since: datetime, limit: int) -> list[Article]:
        """Fetch news articles published since the given time."""


class MarketDataProvider(ABC):
    """Port for market price and volume data."""

    @abstractmethod
    async def get_price_data(self, symbol: str, *, lookback_days: int) -> PriceSeries:
        """Fetch OHLCV price data for a symbol."""

    @abstractmethod
    async def get_volume_data(self, symbol: str, *, lookback_days: int) -> VolumeSeries:
        """Fetch volume data for a symbol."""


class LLMProvider(ABC):
    """Port for LLM-assisted extraction and analysis (not ranking)."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Provider identifier for diagnostics."""

    @abstractmethod
    async def extract_stocks(self, articles: list[Article]) -> list[ExtractedStock]:
        """Extract listed Indian companies mentioned in news."""

    @abstractmethod
    async def analyze_news_llm(
        self,
        articles: list[Article],
        stocks: list[Stock],
        *,
        taxonomy: list | None = None,
        symbol_article_map: dict[str, list] | None = None,
        rag_context: list[str] | None = None,
    ) -> list:
        """Analyze news and return structured LLM sentiment DTOs."""

    @abstractmethod
    async def analyze_news(
        self,
        articles: list[Article],
        stocks: list[Stock],
        *,
        taxonomy: list | None = None,
        symbol_article_map: dict[str, list] | None = None,
        rag_context: list[str] | None = None,
    ) -> list[SentimentAnalysis]:
        """Analyze news sentiment for identified stocks."""

    async def reclassify_catalysts(
        self,
        requests: list,
        *,
        taxonomy_codes: list[str] | None = None,
    ) -> list:
        """Batch reclassify OTHER catalysts against taxonomy codes."""
        from morning_trading_agent.domain.entities.llm_sentiment import (
            CatalystReclassificationResult,
        )

        return [
            CatalystReclassificationResult(symbol=request.symbol, catalyst_code="OTHER")
            for request in requests
        ]

    @abstractmethod
    async def generate_report(
        self, watchlist: Watchlist, candidates: list[TradingCandidate]
    ) -> str:
        """Generate a professional markdown report (narrative only)."""


class NotificationProvider(ABC):
    """Port for sending notifications."""

    @abstractmethod
    async def send_message(self, message: str) -> None:
        """Send a message to the configured channel."""
