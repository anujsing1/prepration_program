"""Evaluate recommendation EOD returns use case."""

from datetime import date

import structlog

from morning_trading_agent.application.services.analytics.daily_evaluation_service import (
    DailyEvaluationReport,
    DailyEvaluationService,
)
from morning_trading_agent.application.services.recommendation_return_service import (
    RecommendationReturnService,
)
from morning_trading_agent.config.container import Container


class EvaluateRecommendationsUseCase:
    """Post-market evaluation of recommendation returns and analytics."""

    def __init__(self, container: Container) -> None:
        self._container = container
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def execute(self, *, trade_date: date) -> DailyEvaluationReport:
        """Compute returns then build analytics report."""
        session = await self._container.get_session()
        try:
            from morning_trading_agent.config.factories.repository_factory import RepositoryFactory
            from morning_trading_agent.config.factories.provider_factory import ProviderFactory

            repo_factory = RepositoryFactory(session)
            recommendation_repo = repo_factory.create_recommendation_result_repository()
            market_provider = ProviderFactory(self._container.settings).create_market_provider()

            return_service = RecommendationReturnService(
                recommendation_repo,
                market_provider,
                lookback_days=self._container.settings.app.technical_lookback_days,
            )
            await return_service.evaluate_trade_date(trade_date)

            analytics = DailyEvaluationService(recommendation_repo)
            report = await analytics.evaluate(trade_date)
            self._logger.info(
                "evaluation_complete",
                trade_date=str(trade_date),
                evaluated=report.evaluated_count,
                win_rate=report.win_rate,
            )
            return report
        finally:
            await session.close()
            await self._container.dispose()
