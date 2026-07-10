"""Repository factory."""

from sqlalchemy.ext.asyncio import AsyncSession

from morning_trading_agent.domain.repositories.article_repository import (
    AnalysisRepository,
    ArticleRepository,
    WatchlistRepository,
)
from morning_trading_agent.domain.repositories.catalyst_taxonomy_repository import (
    CatalystTaxonomyRepository,
)
from morning_trading_agent.domain.repositories.ranking_audit_repository import RankingAuditRepository
from morning_trading_agent.domain.repositories.recommendation_result_repository import (
    RecommendationResultRepository,
)
from morning_trading_agent.infrastructure.database.repositories.analysis_repository import (
    SqlAlchemyAnalysisRepository,
)
from morning_trading_agent.infrastructure.database.repositories.article_repository import (
    SqlAlchemyArticleRepository,
)
from morning_trading_agent.infrastructure.database.repositories.catalyst_taxonomy_repository import (
    SqlAlchemyCatalystTaxonomyRepository,
)
from morning_trading_agent.domain.repositories.catalyst_type_stats_repository import (
    CatalystTypeStatsRepository,
)
from morning_trading_agent.infrastructure.database.repositories.catalyst_type_stats_repository import (
    SqlAlchemyCatalystTypeStatsRepository,
)
from morning_trading_agent.infrastructure.database.repositories.ranking_audit_repository import (
    SqlAlchemyRankingAuditRepository,
)
from morning_trading_agent.infrastructure.database.repositories.recommendation_result_repository import (
    SqlAlchemyRecommendationResultRepository,
)
from morning_trading_agent.infrastructure.database.repositories.watchlist_repository import (
    SqlAlchemyWatchlistRepository,
)


class RepositoryFactory:
    """Creates repository instances bound to a database session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def create_article_repository(self) -> ArticleRepository:
        return SqlAlchemyArticleRepository(self._session)

    def create_analysis_repository(self) -> AnalysisRepository:
        return SqlAlchemyAnalysisRepository(self._session)

    def create_watchlist_repository(self) -> WatchlistRepository:
        return SqlAlchemyWatchlistRepository(self._session)

    def create_ranking_audit_repository(self) -> RankingAuditRepository:
        return SqlAlchemyRankingAuditRepository(self._session)

    def create_recommendation_result_repository(self) -> RecommendationResultRepository:
        return SqlAlchemyRecommendationResultRepository(self._session)

    def create_catalyst_taxonomy_repository(self) -> CatalystTaxonomyRepository:
        return SqlAlchemyCatalystTaxonomyRepository(self._session)

    def create_catalyst_type_stats_repository(self) -> CatalystTypeStatsRepository:
        return SqlAlchemyCatalystTypeStatsRepository(self._session)
