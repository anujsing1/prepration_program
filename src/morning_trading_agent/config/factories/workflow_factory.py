"""Builds NodeFactory with domain-grouped dependencies."""

import structlog

from sqlalchemy.ext.asyncio import AsyncSession

from morning_trading_agent.application.services.adaptive_impact_filter_service import (
    AdaptiveImpactFilterService,
)
from morning_trading_agent.application.services.adaptive_threshold_service import (
    AdaptiveThresholdService,
)
from morning_trading_agent.application.services.catalyst.catalyst_type_stats_service import (
    CatalystTypeStatsService,
)
from morning_trading_agent.application.services.rag.catalyst_rag_service import CatalystRagService
from morning_trading_agent.application.services.rag.embedding_provider import (
    KeywordEmbeddingProvider,
    create_embedding_provider,
)
from morning_trading_agent.infrastructure.database.repositories.in_memory_catalyst_type_stats_repository import (
    InMemoryCatalystTypeStatsRepository,
)
from morning_trading_agent.application.services.beneficiary.beneficiary_extraction_service import (
    BeneficiaryExtractionService,
    NullBeneficiaryExtractionService,
)
from morning_trading_agent.application.services.beneficiary.enhanced_beneficiary_extraction_service import (
    EnhancedBeneficiaryExtractionService,
)
from morning_trading_agent.application.services.catalyst.verified_catalyst_classification_service import (
    VerifiedCatalystClassificationService,
)
from morning_trading_agent.application.services.candidate_filter_service import (
    CandidateFilterService,
)
from morning_trading_agent.application.services.candidate_rejection_logger import (
    CandidateRejectionLogger,
)
from morning_trading_agent.application.services.catalyst.catalyst_classification_service import (
    CatalystClassificationService,
)
from morning_trading_agent.application.services.catalyst.catalyst_reclassification_service import (
    CatalystReclassificationService,
)
from morning_trading_agent.application.services.catalyst.catalyst_scoring_service import (
    CatalystScoringService,
)
from morning_trading_agent.application.services.catalyst.catalyst_taxonomy_cache import (
    CatalystTaxonomyCache,
)
from morning_trading_agent.application.services.catalyst.catalyst_taxonomy_discovery_service import (
    CatalystTaxonomyDiscoveryService,
)
from morning_trading_agent.application.services.catalyst.catalyst_taxonomy_seed_loader import (
    load_catalyst_taxonomy_seed,
)
from morning_trading_agent.application.services.catalyst.catalyst_tier_service import (
    CatalystTierService,
)
from morning_trading_agent.application.services.ingress.article_ingress_filter_service import (
    ArticleIngressFilterService,
)
from morning_trading_agent.application.services.ingress.event_cluster_service import (
    EventClusterService,
)
from morning_trading_agent.application.services.pipeline_metrics_service import (
    PipelineMetricsService,
)
from morning_trading_agent.application.services.professional_trader_gate_service import (
    ProfessionalTraderGateService,
)
from morning_trading_agent.application.services.recommendation_persistence_service import (
    RecommendationPersistenceService,
)
from morning_trading_agent.application.services.technical_analysis_service import (
    TechnicalAnalysisService,
)
from morning_trading_agent.application.services.tiered_watchlist_selector import (
    TieredWatchlistSelector,
)
from morning_trading_agent.application.services.watchlist_pipeline_service import (
    WatchlistPipelineService,
)
from morning_trading_agent.application.services.watchlist_quality_filter import (
    WatchlistQualityFilterService,
)
from morning_trading_agent.config.factories.catalyst_quality_factory import CatalystQualityFactory
from morning_trading_agent.config.factories.llm_factory import LLMFactory
from morning_trading_agent.config.factories.node_factory import NodeFactory
from morning_trading_agent.config.factories.provider_factory import ProviderFactory
from morning_trading_agent.config.factories.repository_factory import RepositoryFactory
from morning_trading_agent.config.factories.strategy_factory import StrategyFactory
from morning_trading_agent.config.premarket_config import ProgressiveRelaxationConfig
from morning_trading_agent.config.settings import Settings
from morning_trading_agent.config.feature_flags import get_feature_flags
from morning_trading_agent.domain.repositories.article_repository import (
    AnalysisRepository,
    ArticleRepository,
    WatchlistRepository,
)
from morning_trading_agent.domain.repositories.ranking_audit_repository import RankingAuditRepository
from morning_trading_agent.domain.repositories.recommendation_result_repository import (
    RecommendationResultRepository,
)
from morning_trading_agent.infrastructure.database.repositories.in_memory_catalyst_taxonomy_repository import (
    InMemoryCatalystTaxonomyRepository,
)
from morning_trading_agent.infrastructure.database.repositories.null_ranking_audit_repository import (
    NullRankingAuditRepository,
)
from morning_trading_agent.infrastructure.database.repositories.null_recommendation_result_repository import (
    NullRecommendationResultRepository,
)
from morning_trading_agent.infrastructure.database.repositories.null_repositories import (
    NullAnalysisRepository,
    NullArticleRepository,
    NullWatchlistRepository,
)
from morning_trading_agent.infrastructure.providers.market.symbol_resolver import SymbolResolver


class WorkflowFactory:
    """Domain-grouped factory for workflow node construction."""

    def __init__(
        self,
        settings: Settings,
        *,
        dry_run: bool,
        provider_factory: ProviderFactory,
        llm_factory: LLMFactory,
        strategy_factory: StrategyFactory,
        catalyst_classification: CatalystClassificationService,
        symbol_resolver: SymbolResolver,
    ) -> None:
        self._settings = settings
        self._dry_run = dry_run
        self._provider_factory = provider_factory
        self._llm_factory = llm_factory
        self._strategy_factory = strategy_factory
        self._catalyst_classification = catalyst_classification
        self._symbol_resolver = symbol_resolver
        self._resolved_runtime = settings.resolved_runtime
        self._logger = structlog.get_logger(self.__class__.__name__)

    def _create_beneficiary_service(
        self, llm
    ) -> BeneficiaryExtractionService | NullBeneficiaryExtractionService:
        """Wire beneficiary extraction from composition root (never in workflow nodes)."""
        if not self._settings.app.beneficiary_extraction_enabled:
            return NullBeneficiaryExtractionService()

        service: BeneficiaryExtractionService = BeneficiaryExtractionService(
            resolver=self._symbol_resolver,
            llm=llm,
            config=self._settings.beneficiary_extraction_config,
        )
        flags = get_feature_flags()
        if flags.enable_beneficiary_agent:
            from morning_trading_agent.agents.beneficiary.beneficiary_discovery_agent import (
                BeneficiaryDiscoveryAgent,
            )

            service = EnhancedBeneficiaryExtractionService(
                base=service,
                discovery_agent=BeneficiaryDiscoveryAgent(resolver=self._symbol_resolver),
            )
        return service

    async def create_node_factory(
        self, session: AsyncSession | None = None
    ) -> NodeFactory:
        """Wire all dependencies and return a NodeFactory."""
        use_null_repos = self._dry_run or not self._settings.database_enabled
        use_null_notifier = self._dry_run or not self._settings.telegram_enabled
        llm = self._llm_factory.create_llm_provider(allow_stub=self._dry_run)

        if use_null_repos:
            article_repo: ArticleRepository = NullArticleRepository()
            analysis_repo: AnalysisRepository = NullAnalysisRepository()
            watchlist_repo: WatchlistRepository = NullWatchlistRepository()
            ranking_audit_repo: RankingAuditRepository = NullRankingAuditRepository()
            recommendation_repo: RecommendationResultRepository = (
                NullRecommendationResultRepository()
            )
        else:
            if session is None:
                raise ValueError("Database session required when ENABLE_DATABASE=true")
            repo_factory = RepositoryFactory(session)
            article_repo = repo_factory.create_article_repository()
            analysis_repo = repo_factory.create_analysis_repository()
            watchlist_repo = repo_factory.create_watchlist_repository()
            ranking_audit_repo = repo_factory.create_ranking_audit_repository()
            recommendation_repo = repo_factory.create_recommendation_result_repository()

        if self._dry_run:
            from morning_trading_agent.infrastructure.providers.market.stub_market_provider import (
                StubMarketDataProvider,
            )

            market_provider = StubMarketDataProvider()
        else:
            market_provider = self._provider_factory.create_market_provider()

        technical_service = TechnicalAnalysisService(
            market_provider,
            lookback_days=self._settings.app.technical_lookback_days,
            session_mode=self._resolved_runtime.detected_session,
            weight_config=self._settings.technical_weight_config,
            sector_config=self._settings.sector_momentum_config,
        )
        tier_service = CatalystTierService()
        rejection_logger = CandidateRejectionLogger(tier_service=tier_service)
        quality_filter = WatchlistQualityFilterService(
            config=self._settings.watchlist_quality_config,
            rejection_logger=rejection_logger,
            tradability_config=self._settings.tradability_score_config,
        )
        ingress_filter = ArticleIngressFilterService(
            config=self._settings.ingress_filter_config
        )
        beneficiary_service = self._create_beneficiary_service(llm)
        flags = get_feature_flags()
        catalyst_classification = self._catalyst_classification
        scoring_service = self._catalyst_classification._scoring
        taxonomy_cache: CatalystTaxonomyCache | None = None
        if flags.enable_db_catalyst_taxonomy:
            if session is not None:
                taxonomy_repo = RepositoryFactory(session).create_catalyst_taxonomy_repository()
                source = "db"
            else:
                taxonomy_repo = InMemoryCatalystTaxonomyRepository()
                source = "memory"
            taxonomy_cache = CatalystTaxonomyCache(taxonomy_repo, source=source)
            seed = load_catalyst_taxonomy_seed()
            taxonomy_cache.set_aliases(seed.aliases)
            await taxonomy_cache.load()
            scoring_service = CatalystScoringService(
                score_config=self._settings.catalyst_score_config,
                taxonomy_cache=taxonomy_cache,
                use_db_taxonomy=True,
            )
            discovery = CatalystTaxonomyDiscoveryService(
                repository=taxonomy_repo,
                cache=taxonomy_cache,
            )
            reclassification = CatalystReclassificationService(
                llm=llm,
                taxonomy_cache=taxonomy_cache,
                scoring_service=scoring_service,
                enabled=flags.enable_catalyst_reclassification,
            )
            catalyst_classification = CatalystClassificationService(
                scoring_service=scoring_service,
                taxonomy_discovery=discovery,
                taxonomy_cache=taxonomy_cache,
                reclassification_service=reclassification,
                use_db_taxonomy=True,
            )
        elif flags.enable_catalyst_reclassification:
            reclassification = CatalystReclassificationService(
                llm=llm,
                scoring_service=scoring_service,
                enabled=True,
            )
            catalyst_classification = CatalystClassificationService(
                scoring_service=scoring_service,
                reclassification_service=reclassification,
            )
        if flags.enable_catalyst_verifier:
            from morning_trading_agent.agents.catalyst.catalyst_verification_agent import (
                CatalystVerificationAgent,
            )

            catalyst_classification = VerifiedCatalystClassificationService(
                base=catalyst_classification,
                verifier=CatalystVerificationAgent(),
            )
        professional_gate = ProfessionalTraderGateService(
            config=self._settings.professional_trader_gate_config
        )
        pipeline_metrics = PipelineMetricsService()
        event_cluster = EventClusterService()
        trading_profile = self._settings.trading_profile_config
        catalyst_quality_factory = CatalystQualityFactory(self._settings)
        if session is not None:
            stats_repo = RepositoryFactory(session).create_catalyst_type_stats_repository()
        else:
            stats_repo = InMemoryCatalystTypeStatsRepository()
        stats_service = CatalystTypeStatsService(stats_repo)
        catalyst_rag: CatalystRagService | None = None
        if flags.enable_catalyst_rag:
            if self._dry_run:
                rag_embedder = KeywordEmbeddingProvider()
            else:
                rag_embedder = create_embedding_provider(
                    self._settings,
                    provider_name=self._settings.app.llm_provider,
                    embedding_model=self._settings.rag.embedding_model,
                )
            catalyst_rag = CatalystRagService(
                self._settings,
                embedder=rag_embedder,
                stats_service=stats_service,
                top_k=self._settings.rag.top_k,
                enabled=True,
            )
        impact_scoring = catalyst_quality_factory.create_impact_scoring_service()
        impact_assessment = catalyst_quality_factory.create_impact_assessment_service(
            stats_service=stats_service,
        )
        adaptive_filter = AdaptiveImpactFilterService(
            profile=trading_profile,
            threshold_service=AdaptiveThresholdService(
                config=self._settings.adaptive_threshold_config,
                impact_scoring=impact_scoring,
            ),
            rejection_logger=rejection_logger,
        )
        tiered_selector = TieredWatchlistSelector(
            profile=trading_profile,
            gate=professional_gate,
            gate_config=self._settings.professional_trader_gate_config,
        )
        recommendation_persistence = RecommendationPersistenceService(recommendation_repo)

        return NodeFactory(
            settings=self._settings,
            aggregator=self._provider_factory.create_news_aggregator_service(
                self._resolved_runtime
            ),
            llm=llm,
            notifier=self._provider_factory.create_notification_provider(
                use_null=use_null_notifier
            ),
            technical_service=technical_service,
            ranking_strategy=self._strategy_factory.create_ranking_strategy(
                self._resolved_runtime.effective_strategy
            ),
            effective_strategy=self._resolved_runtime.effective_strategy,
            detected_session=self._resolved_runtime.detected_session,
            candidate_filter=adaptive_filter,
            ingress_filter=ingress_filter,
            beneficiary_service=beneficiary_service,
            event_cluster=event_cluster,
            professional_gate=professional_gate,
            trading_profile=trading_profile,
            tiered_selector=tiered_selector,
            pipeline_metrics=pipeline_metrics,
            catalyst_classification=catalyst_classification,
            catalyst_quality_enrichment=catalyst_quality_factory.create_enrichment_service(
                scoring_service=scoring_service
            ),
            catalyst_impact_assessment=impact_assessment,
            catalyst_type_stats=stats_service,
            catalyst_rag=catalyst_rag,
            symbol_resolver=self._symbol_resolver,
            article_repo=article_repo,
            analysis_repo=analysis_repo,
            watchlist_repo=watchlist_repo,
            ranking_audit_repo=ranking_audit_repo,
            recommendation_repo=recommendation_repo,
            recommendation_persistence=recommendation_persistence,
            persist_enabled=self._settings.database_enabled and not self._dry_run,
            telegram_enabled=self._settings.telegram_enabled and not self._dry_run,
        )
