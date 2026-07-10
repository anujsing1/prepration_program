"""Provider factory for creating external service adapters."""

from pathlib import Path

from morning_trading_agent.application.ports.providers import (
    MarketDataProvider,
    NewsProvider,
    NotificationProvider,
)
from morning_trading_agent.application.services.market.nse_trading_calendar import (
    NSETradingCalendar,
)
from morning_trading_agent.application.services.news.catalyst_analysis_service import (
    CatalystAnalysisService,
)
from morning_trading_agent.application.services.news.freshness_filter import FreshnessFilter
from morning_trading_agent.application.services.news.freshness_scoring_service import (
    FreshnessScoringService,
)
from morning_trading_agent.application.services.news.news_aggregator_service import (
    NewsAggregatorService,
)
from morning_trading_agent.application.services.news.news_deduplication import NewsDeduplication
from morning_trading_agent.application.services.news.news_priority_service import NewsPriorityService
from morning_trading_agent.application.services.news.news_quality_scorer import NewsQualityScorer
from morning_trading_agent.config.settings import Settings
from morning_trading_agent.domain.value_objects.resolved_runtime import ResolvedRuntimeConfig
from morning_trading_agent.infrastructure.providers.market.nse_market_provider import (
    NSEMarketProvider,
)
from morning_trading_agent.infrastructure.providers.news.economic_times_adapter import (
    EconomicTimesAdapter,
)
from morning_trading_agent.infrastructure.providers.news.google_news_adapter import GoogleNewsAdapter
from morning_trading_agent.infrastructure.providers.news.moneycontrol_adapter import (
    MoneycontrolAdapter,
)
from morning_trading_agent.infrastructure.providers.news.nse_announcements_adapter import (
    NSEAnnouncementsAdapter,
)
from morning_trading_agent.infrastructure.telegram.telegram_adapter import TelegramAdapter


class ProviderFactory:
    """Creates provider adapter instances from settings."""

    _NEWS_ADAPTERS: dict[str, type[NewsProvider]] = {
        "moneycontrol": MoneycontrolAdapter,
        "economic_times": EconomicTimesAdapter,
        "google_news": GoogleNewsAdapter,
        "nse_announcements": NSEAnnouncementsAdapter,
    }

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def create_trading_calendar(self) -> NSETradingCalendar:
        """Build NSE calendar with YAML holidays and configured market hours."""
        market_hours = self._settings.market_hours
        path = Path(self._settings.app.nse_holidays_path)
        if path.is_file():
            return NSETradingCalendar.from_yaml(path, market_hours=market_hours)
        return NSETradingCalendar(market_hours=market_hours)

    def create_news_providers(self) -> list[NewsProvider]:
        """Create configured news provider adapters."""
        providers: list[NewsProvider] = []
        for name in self._settings.news_provider_list:
            adapter_cls = self._NEWS_ADAPTERS.get(name)
            if adapter_cls:
                providers.append(adapter_cls())
        return providers

    def create_news_aggregator_service(
        self,
        resolved_runtime: ResolvedRuntimeConfig | None = None,
    ) -> NewsAggregatorService:
        """Create news aggregator service with filtering and deduplication."""
        runtime = resolved_runtime or self._settings.resolved_runtime
        calendar = self.create_trading_calendar()
        use_session = self._settings.app.use_session_freshness
        return NewsAggregatorService(
            providers=self.create_news_providers(),
            freshness_filter=FreshnessFilter(
                window_hours=self._settings.app.news_freshness_hours,
                calendar=calendar,
                use_session_freshness=use_session,
                future_tolerance_minutes=self._settings.app.future_date_tolerance_minutes,
            ),
            deduplication=NewsDeduplication(),
            freshness_scorer=FreshnessScoringService(
                threshold_config=self._settings.freshness_threshold_config,
                calendar=calendar,
                use_session_freshness=use_session,
            ),
            catalyst_analysis=CatalystAnalysisService(
                score_config=self._settings.catalyst_score_config
            ),
            priority_service=NewsPriorityService(),
            news_quality_scorer=NewsQualityScorer(
                config=self._settings.news_quality_config
            ),
            calendar=calendar,
            trading_session=runtime.detected_session,
            fetch_lookback_hours=float(self._settings.app.news_lookback_hours),
            use_session_freshness=use_session,
            fetch_buffer_minutes=self._settings.app.session_fetch_buffer_minutes,
        )

    def create_market_provider(self) -> MarketDataProvider:
        """Create NSE market data provider."""
        return NSEMarketProvider(market_data_source=self._settings.app.market_data_source)

    def create_notification_provider(self, *, use_null: bool = False) -> NotificationProvider:
        """Create Telegram or null notification provider."""
        if use_null:
            from morning_trading_agent.infrastructure.telegram.null_adapter import (
                NullNotificationProvider,
            )

            return NullNotificationProvider()
        return TelegramAdapter(self._settings.telegram)
