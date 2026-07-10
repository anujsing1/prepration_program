"""Graph node factory."""

from morning_trading_agent.application.builders.candidate_explanation_builder import (
    CandidateExplanationBuilder,
)
from morning_trading_agent.application.builders.watchlist_report_builder import (
    WatchlistReportBuilder,
)
from morning_trading_agent.application.ports.providers import LLMProvider, NotificationProvider
from morning_trading_agent.application.ranking.strategies import RankingStrategy
from morning_trading_agent.application.services.adaptive_impact_filter_service import (
    AdaptiveImpactFilterService,
)
from morning_trading_agent.application.services.beneficiary.beneficiary_extraction_service import (
    BeneficiaryExtractionService,
)
from morning_trading_agent.application.services.catalyst.catalyst_impact_assessment_service import (
    CatalystImpactAssessmentService,
)
from morning_trading_agent.application.services.catalyst.catalyst_type_stats_service import (
    CatalystTypeStatsService,
)
from morning_trading_agent.application.services.catalyst.catalyst_classification_service import (
    CatalystClassificationService,
)
from morning_trading_agent.application.services.catalyst_quality.catalyst_quality_enrichment_service import (
    CatalystQualityEnrichmentService,
)
from morning_trading_agent.application.services.ingress.article_ingress_filter_service import (
    ArticleIngressFilterService,
)
from morning_trading_agent.application.services.ingress.event_cluster_service import (
    EventClusterService,
)
from morning_trading_agent.application.services.news.news_aggregator_service import (
    NewsAggregatorService,
)
from morning_trading_agent.application.services.pipeline_metrics_service import (
    PipelineMetricsService,
)
from morning_trading_agent.application.services.professional_trader_gate_service import (
    ProfessionalTraderGateService,
)
from morning_trading_agent.application.services.pipeline.score_validator import ScoreValidator
from morning_trading_agent.application.services.ranking_pipeline_audit_service import (
    RankingPipelineAuditService,
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
from morning_trading_agent.config.premarket_config import TradingProfileConfig
from morning_trading_agent.config.settings import Settings
from morning_trading_agent.domain.repositories.article_repository import (
    AnalysisRepository,
    ArticleRepository,
    WatchlistRepository,
)
from morning_trading_agent.domain.repositories.ranking_audit_repository import RankingAuditRepository
from morning_trading_agent.domain.repositories.recommendation_result_repository import (
    RecommendationResultRepository,
)
from morning_trading_agent.domain.value_objects.trading_session import TradingSessionMode
from morning_trading_agent.graph.nodes.base import GraphNode
from morning_trading_agent.application.services.rag.catalyst_rag_service import CatalystRagService
from morning_trading_agent.graph.workflows.news.builder import NewsWorkflowBuilder
from morning_trading_agent.graph.workflows.ranking.builder import RankingWorkflowBuilder
from morning_trading_agent.graph.workflows.graph_config import WorkflowGraphConfig, WorkflowGraphStore
from morning_trading_agent.graph.workflows.registry import WorkflowRegistry
from morning_trading_agent.graph.workflows.reporting.builder import ReportingWorkflowBuilder
from morning_trading_agent.graph.workflows.research.builder import ResearchWorkflowBuilder
from morning_trading_agent.graph.workflows.technical.builder import TechnicalWorkflowBuilder
from morning_trading_agent.graph.workflows.watchlist.builder import WatchlistWorkflowBuilder
from morning_trading_agent.infrastructure.providers.market.symbol_resolver import SymbolResolver


class NodeFactory:
    """Creates LangGraph workflow nodes with injected dependencies."""

    def __init__(
        self,
        settings: Settings,
        aggregator: NewsAggregatorService,
        llm: LLMProvider,
        notifier: NotificationProvider,
        technical_service: TechnicalAnalysisService,
        ranking_strategy: RankingStrategy,
        effective_strategy: str,
        detected_session: TradingSessionMode,
        candidate_filter: AdaptiveImpactFilterService,
        ingress_filter: ArticleIngressFilterService,
        beneficiary_service: BeneficiaryExtractionService,
        event_cluster: EventClusterService,
        professional_gate: ProfessionalTraderGateService,
        trading_profile: TradingProfileConfig,
        tiered_selector: TieredWatchlistSelector,
        pipeline_metrics: PipelineMetricsService,
        catalyst_classification: CatalystClassificationService,
        catalyst_quality_enrichment: CatalystQualityEnrichmentService,
        catalyst_impact_assessment: CatalystImpactAssessmentService,
        symbol_resolver: SymbolResolver,
        article_repo: ArticleRepository,
        analysis_repo: AnalysisRepository,
        watchlist_repo: WatchlistRepository,
        ranking_audit_repo: RankingAuditRepository,
        recommendation_repo: RecommendationResultRepository,
        recommendation_persistence: RecommendationPersistenceService,
        *,
        catalyst_rag: CatalystRagService | None = None,
        catalyst_type_stats: CatalystTypeStatsService | None = None,
        persist_enabled: bool = True,
        telegram_enabled: bool = True,
    ) -> None:
        self._settings = settings
        self._aggregator = aggregator
        self._llm = llm
        self._notifier = notifier
        self._technical_service = technical_service
        self._ranking_strategy = ranking_strategy
        self._effective_strategy = effective_strategy
        self._detected_session = detected_session
        self._candidate_filter = candidate_filter
        self._ingress_filter = ingress_filter
        self._beneficiary = beneficiary_service
        self._event_cluster = event_cluster
        self._professional_gate = professional_gate
        self._trading_profile = trading_profile
        self._tiered_selector = tiered_selector
        self._pipeline_metrics = pipeline_metrics
        self._catalyst_classification = catalyst_classification
        self._catalyst_quality_enrichment = catalyst_quality_enrichment
        self._catalyst_impact_assessment = catalyst_impact_assessment
        self._catalyst_rag = catalyst_rag
        self._catalyst_type_stats = catalyst_type_stats
        self._symbol_resolver = symbol_resolver
        self._article_repo = article_repo
        self._analysis_repo = analysis_repo
        self._watchlist_repo = watchlist_repo
        self._ranking_audit_repo = ranking_audit_repo
        self._recommendation_repo = recommendation_repo
        self._recommendation_persistence = recommendation_persistence
        self._report_builder = WatchlistReportBuilder()
        self._explanation_builder = CandidateExplanationBuilder()
        self._pipeline_audit = RankingPipelineAuditService()
        self._score_validator = ScoreValidator()
        self._persist_enabled = persist_enabled
        self._telegram_enabled = telegram_enabled

    def create_registry(self, graph_config: WorkflowGraphConfig | None = None) -> WorkflowRegistry:
        """Build the modular workflow registry."""
        registry = WorkflowRegistry(
            news=NewsWorkflowBuilder(
                self._aggregator,
                self._ingress_filter,
                self._settings.app,
            ),
            research=ResearchWorkflowBuilder(
                self._beneficiary,
                self._event_cluster,
                self._llm,
                self._catalyst_classification,
                self._catalyst_quality_enrichment,
                self._catalyst_impact_assessment,
                catalyst_rag=self._catalyst_rag,
            ),
            technical=TechnicalWorkflowBuilder(self._technical_service),
            ranking=RankingWorkflowBuilder(
                self._ranking_strategy,
                self._pipeline_audit,
                self._explanation_builder,
                self._score_validator,
            ),
            watchlist=WatchlistWorkflowBuilder(
                self._settings,
                self._candidate_filter,
                self._pipeline_audit,
                self._professional_gate,
                self._trading_profile,
                self._tiered_selector,
                stats_service=self._catalyst_type_stats,
            ),
            reporting=ReportingWorkflowBuilder(
                self._settings.app,
                self._llm,
                self._notifier,
                self._pipeline_metrics,
                self._explanation_builder,
                self._report_builder,
                self._article_repo,
                self._analysis_repo,
                self._watchlist_repo,
                self._ranking_audit_repo,
                self._recommendation_persistence,
                self._effective_strategy,
                self._detected_session,
                persist_enabled=self._persist_enabled,
                telegram_enabled=self._telegram_enabled,
                persist_all_filtered=self._settings.app.persist_all_filtered_candidates,
            ),
        )
        return registry

    def create_nodes(self, graph_config: WorkflowGraphConfig | None = None) -> list[GraphNode]:
        """Create all workflow nodes in execution order via modular registry."""
        config = graph_config or WorkflowGraphStore().load()
        return self.create_registry(graph_config=config).build_all_nodes(graph_config=config)

    def create_workflow_nodes(
        self,
        workflow: str,
        graph_config: WorkflowGraphConfig | None = None,
    ) -> list[GraphNode]:
        """Create nodes for a single workflow module."""
        config = graph_config or WorkflowGraphStore().load()
        return self.create_registry(graph_config=config).build_workflow_nodes(
            workflow,
            graph_config=config,
        )
