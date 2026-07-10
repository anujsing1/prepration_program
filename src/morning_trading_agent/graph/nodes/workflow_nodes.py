"""LangGraph workflow node implementations."""

from datetime import UTC, datetime

import structlog

from morning_trading_agent.application.builders.candidate_explanation_builder import (
    CandidateExplanationBuilder,
)
from morning_trading_agent.application.builders.ranking_audit_builder import RankingAuditBuilder
from morning_trading_agent.application.builders.watchlist_report_builder import (
    WatchlistReportBuilder,
)
from morning_trading_agent.application.ports.providers import LLMProvider, NotificationProvider
from morning_trading_agent.application.ranking.strategies import RankingStrategy
from morning_trading_agent.application.services.beneficiary.beneficiary_extraction_service import (
    BeneficiaryExtractionService,
)
from morning_trading_agent.application.services.event.event_beneficiary_service import (
    EventBeneficiaryService,
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
from morning_trading_agent.application.ranking.institutional_ranking_strategy import (
    InstitutionalRankingStrategy,
)
from morning_trading_agent.application.ranking.institutional_ranking_strategy_v4 import (
    InstitutionalRankingStrategyV4,
)
from morning_trading_agent.agents.market.market_context_agent import MarketContextAgent
from morning_trading_agent.application.services.adaptive_impact_filter_service import (
    AdaptiveImpactFilterService,
)
from morning_trading_agent.application.services.catalyst.catalyst_impact_assessment_service import (
    CatalystImpactAssessmentService,
)
from morning_trading_agent.application.services.llm.resilient_news_analysis_service import (
    ResilientNewsAnalysisService,
)
from morning_trading_agent.application.services.rag.catalyst_rag_service import CatalystRagService
from morning_trading_agent.application.services.pipeline.tradability_resolver import (
    tradability_shadow_payload,
)
from morning_trading_agent.application.services.pipeline.score_safety import (
    candidate_adjusted_score,
    candidate_final_score,
)
from morning_trading_agent.application.services.pipeline.candidate_audit_service import (
    load_from_state,
    persist_to_state,
)
from morning_trading_agent.application.services.pipeline.pipeline_stages import (
    CATALYST_CLASSIFICATION,
    RANKING,
    SCORE_VALIDATION,
    TECHNICAL_ANALYSIS,
)
from morning_trading_agent.application.services.pipeline.score_validator import ScoreValidator
from morning_trading_agent.application.services.pipeline.stage_audit_recorder import record_stage
from morning_trading_agent.domain.value_objects.rejection_reasons import (
    MISSING_CATALYST_DATA,
    MISSING_TECHNICAL_DATA,
)
from morning_trading_agent.config.premarket_config import TradingProfileConfig
from morning_trading_agent.application.services.near_miss_review_service import (
    NearMissReviewService,
)
from morning_trading_agent.application.services.catalyst_quality.catalyst_quality_enrichment_service import (
    CatalystQualityEnrichmentService,
)
from morning_trading_agent.domain.value_objects.catalyst_tradability import (
    AcceptedCatalystDiagnostic,
)
from morning_trading_agent.application.services.ranking_pipeline_audit_service import (
    RankingPipelineAuditService,
)
from morning_trading_agent.application.services.catalyst.catalyst_classification_service import (
    CatalystClassificationService,
)
from morning_trading_agent.application.services.catalyst.catalyst_type_stats_service import (
    CatalystTypeStatsService,
)
from morning_trading_agent.application.services.tiered_watchlist_selector import (
    TieredWatchlistSelector,
)
from morning_trading_agent.application.services.technical_analysis_service import (
    TechnicalAnalysisService,
)
from morning_trading_agent.application.services.startup_diagnostics import StartupDiagnosticsService
from morning_trading_agent.application.services.news.article_freshness_utils import ensure_utc
from morning_trading_agent.application.services.recommendation_persistence_service import (
    RecommendationPersistenceService,
)
from morning_trading_agent.config.settings import ApplicationSettings
from morning_trading_agent.domain.entities.article import DailyReport
from morning_trading_agent.domain.exceptions.base import LLMException, ProviderException
from morning_trading_agent.infrastructure.llm.gemini_adapter import is_quota_exhausted_error
from morning_trading_agent.domain.repositories.article_repository import (
    AnalysisRepository,
    ArticleRepository,
    WatchlistRepository,
)
from morning_trading_agent.domain.repositories.ranking_audit_repository import RankingAuditRepository
from morning_trading_agent.domain.value_objects.trading_session import TradingSessionMode
from morning_trading_agent.graph.state import TradingState
from morning_trading_agent.infrastructure.providers.dry_run_fixtures import sample_articles
from morning_trading_agent.infrastructure.providers.market.symbol_resolver import SymbolResolver


class FetchNewsNode:
    """Fetches news from configured providers."""

    name = "fetch_news"

    def __init__(
        self,
        aggregator: NewsAggregatorService,
        settings: ApplicationSettings,
    ) -> None:
        self._aggregator = aggregator
        self._settings = settings
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def execute(self, state: TradingState) -> TradingState:
        articles, stats = await self._aggregator.collect(limit=self._settings.news_fetch_limit)
        using_fixtures = False
        if state["dry_run"] and not articles:
            self._logger.warning("using_dry_run_fixture_articles")
            articles = sample_articles()
            using_fixtures = True
        elif not state["dry_run"] and not articles:
            raise ProviderException("No articles fetched from configured news providers")

        mock_articles = [
            article
            for article in articles
            if article.source in StartupDiagnosticsService.MOCK_ARTICLE_SOURCES
        ]
        if not state["dry_run"] and mock_articles:
            raise ProviderException(
                "Mock/fixture articles detected in live mode — ranking aborted"
            )

        for article in articles:
            published_utc = ensure_utc(article.published_at)
            self._logger.info(
                "article_ingested",
                title=article.title,
                source=article.source,
                published_at=article.published_at.isoformat(),
                published_at_utc=published_utc.isoformat(),
                current_time_utc=datetime.now(UTC).isoformat(),
                computed_age_minutes=article.age_minutes,
                catalyst_type=article.catalyst_type.value,
                catalyst_score=article.catalyst_score,
                priority_score=article.priority_score,
                age_minutes=article.age_minutes,
                freshness_band=article.freshness_band,
                fixture=article.source in StartupDiagnosticsService.MOCK_ARTICLE_SOURCES,
            )

        self._logger.info(
            "fetch_news_complete",
            articles_fetched=stats.articles_fetched,
            articles_removed_freshness=stats.articles_removed_freshness,
            freshness_rejection_counts=stats.freshness_rejection_counts,
            session_window_start=stats.session_window_start.isoformat()
            if stats.session_window_start
            else None,
            session_window_end=stats.session_window_end.isoformat()
            if stats.session_window_end
            else None,
            articles_removed_duplicate=stats.articles_removed_duplicate,
            articles_analyzed=len(articles),
            catalysts_identified=stats.catalysts_identified,
            freshness_distribution=stats.freshness_distribution,
            priority_distribution=stats.priority_distribution,
            using_fixture_articles=using_fixtures,
        )
        state["articles"] = articles
        state["ingestion_stats"] = stats
        return state


class FilterArticlesNode:
    """Pre-LLM ingress quality gate and event clustering."""

    name = "filter_articles"

    def __init__(self, ingress_filter: ArticleIngressFilterService) -> None:
        self._ingress = ingress_filter
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def execute(self, state: TradingState) -> TradingState:
        result = self._ingress.filter(state["articles"])
        run_id = state.get("run_id", "")
        for article in result.accepted:
            self._logger.info(
                "article_accepted",
                run_id=run_id,
                article_id=str(article.id),
                title=article.title,
                source=article.source,
            )
        for article in result.rejected:
            reason = article.ingress_drop_reason or "ingress_rejected"
            self._logger.info(
                "article_rejected",
                run_id=run_id,
                article_id=str(article.id),
                title=article.title,
                source=article.source,
                reason=reason,
            )
        state["articles"] = result.accepted
        state["rejected_articles"] = result.rejected
        state["ingress_rejection_counts"] = result.rejection_reasons
        self._logger.info(
            "filter_articles_complete",
            accepted=len(result.accepted),
            rejected=len(result.rejected),
        )
        return state


class ExtractStocksNode:
    """Extracts primary beneficiaries per article (rule-based + optional LLM)."""

    name = "extract_stocks"

    def __init__(
        self,
        beneficiary_service: BeneficiaryExtractionService,
        event_cluster: EventClusterService,
        *,
        llm_fallback: LLMProvider | None = None,
    ) -> None:
        self._beneficiary = beneficiary_service
        self._events = event_cluster
        self._llm = llm_fallback
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def execute(self, state: TradingState) -> TradingState:
        beneficiary_service = getattr(self, "_beneficiary", None)
        if beneficiary_service is None or not getattr(beneficiary_service, "enabled", True):
            self._logger.warning(
                "beneficiary_extraction_disabled",
                reason="service_not_registered",
            )
            state["identified_stocks"] = []
            state["stock_mentions"] = []
            state["symbol_article_map"] = {}
            state["event_records"] = []
            return state

        mentions, symbol_map = await beneficiary_service.extract(state["articles"])
        stocks = await beneficiary_service.resolve_primary_stocks(mentions)
        run_id = state.get("run_id", "")
        mentions_by_article: dict[str, list] = {}
        for mention in mentions:
            mentions_by_article.setdefault(str(mention.article_id), []).append(mention)
        for article in state["articles"]:
            article_mentions = mentions_by_article.get(str(article.id), [])
            primaries = [m for m in article_mentions if m.beneficiary_rank == 1]
            if primaries:
                self._logger.info(
                    "symbol_extraction_success",
                    run_id=run_id,
                    article_id=str(article.id),
                    title=article.title,
                    primary_symbol=primaries[0].symbol,
                    extraction_method=primaries[0].extraction_method,
                )
            else:
                self._logger.info(
                    "symbol_extraction_failure",
                    run_id=run_id,
                    article_id=str(article.id),
                    title=article.title,
                    failure_reason="no_resolvable_symbol",
                )
        weight_map = {
            m.symbol: m.beneficiary_weight
            for m in mentions
            if m.beneficiary_rank == 1 or m.role.value in ("PRIMARY_BENEFICIARY", "ACQUIRER", "ACQUIREE")
        }
        article_symbols: dict[str, list[str]] = {}
        for mention in mentions:
            article_symbols.setdefault(str(mention.article_id), []).append(mention.symbol)
        events = self._events.build_event_records(
            state["articles"],
            symbol_weights=weight_map,
            article_symbols=article_symbols,
        )
        self._logger.info(
            "extract_stocks_complete",
            extracted_count=len(mentions),
            resolved_count=len(stocks),
            symbols=[stock.symbol for stock in stocks],
        )
        if not state["dry_run"] and state["articles"] and not stocks:
            raise ProviderException(
                "Beneficiary extraction returned no resolvable primary symbols"
            )
        state["identified_stocks"] = stocks
        state["stock_mentions"] = mentions
        state["symbol_article_map"] = {k: list(v) for k, v in symbol_map.items()}
        state["event_records"] = events
        audit = load_from_state(state)
        audit.init_from_stocks(stocks)
        persist_to_state(state, audit)
        return state


class RetrieveCatalystContextNode:
    """Retrieve catalyst taxonomy/examples via RAG for grounded LLM analysis."""

    name = "retrieve_catalyst_context"

    def __init__(self, rag_service: CatalystRagService | None) -> None:
        self._rag = rag_service
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def execute(self, state: TradingState) -> TradingState:
        if self._rag is None or not self._rag.enabled or not state["articles"]:
            state["catalyst_rag_context"] = []
            state["catalyst_rag_hit_count"] = 0
            return state

        results = await self._rag.retrieve_for_articles(state["articles"])
        context = CatalystRagService.format_context(results)
        state["catalyst_rag_context"] = context
        state["catalyst_rag_hit_count"] = len(results)
        self._logger.info(
            "retrieve_catalyst_context_complete",
            hits=len(results),
            run_id=state.get("run_id", ""),
        )
        return state


class AnalyzeNewsNode:
    """Analyzes news sentiment for identified stocks."""

    name = "analyze_news"

    def __init__(
        self,
        llm: LLMProvider,
        catalyst_classification: CatalystClassificationService,
    ) -> None:
        self._llm = llm
        self._catalyst_classification = catalyst_classification
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def execute(self, state: TradingState) -> TradingState:
        if not state["identified_stocks"]:
            state["sentiment_results"] = []
            state["llm_analysis_failures"] = []
            state["llm_analysis_succeeded"] = 0
            state["llm_analysis_failed"] = 0
            return state

        use_db_taxonomy = self._catalyst_classification.use_db_taxonomy
        taxonomy = (
            await self._catalyst_classification.load_taxonomy_entries()
            if use_db_taxonomy
            else None
        )
        symbol_map = state.get("symbol_article_map") or {}
        resilient = ResilientNewsAnalysisService(self._llm)
        analysis = await resilient.analyze(
            state["articles"],
            state["identified_stocks"],
            taxonomy=taxonomy,
            symbol_article_map=symbol_map,
            use_db_taxonomy=use_db_taxonomy,
            rag_context=state.get("catalyst_rag_context") or None,
        )
        state["llm_analysis_failures"] = analysis.failures
        state["llm_analysis_succeeded"] = analysis.succeeded
        state["llm_analysis_failed"] = analysis.failed

        linked_results = []
        for item in analysis.analyses:
            article_ids = getattr(item, "article_ids", None) or []
            if not article_ids and item.symbol in symbol_map:
                linked_results.append(
                    item.model_copy(
                        update={
                            "article_ids": [
                                str(article_id) for article_id in symbol_map[item.symbol]
                            ]
                        }
                    )
                )
            else:
                linked_results.append(item)

        if use_db_taxonomy:
            enriched = await self._catalyst_classification.classify_from_llm_async(
                linked_results, state["articles"]
            )
        elif linked_results:
            enriched = self._catalyst_classification.classify_from_llm(
                linked_results, state["articles"]
            )
        else:
            enriched = []

        run_id = state.get("run_id", "")
        for item in linked_results:
            self._logger.info(
                "classifier_input",
                run_id=run_id,
                symbol=item.symbol,
                catalyst_type=getattr(item, "catalyst_type", None)
                or getattr(item, "primary_catalyst_type", None),
                article_ids=[str(aid) for aid in getattr(item, "article_ids", [])],
            )
        state["pending_catalysts_discovered"] = (
            self._catalyst_classification.pending_discoveries
        )
        self._logger.info(
            "analyze_news_complete",
            llm_provider=self._llm.provider_name,
            analyses_completed=len(enriched),
            llm_analysis_succeeded=analysis.succeeded,
            llm_analysis_failed=analysis.failed,
            symbols=[item.symbol for item in enriched],
            catalyst_types=[item.primary_catalyst_type.value for item in enriched],
        )
        state["sentiment_results"] = enriched

        for item in enriched:
            self._logger.info(
                "classifier_output",
                run_id=run_id,
                symbol=item.symbol,
                final_catalyst_type=item.primary_catalyst_type.value,
                confidence=item.classification_confidence,
                llm_classified=item.llm_classified,
                matched_existing=item.matched_existing,
            )
            if item.primary_catalyst_type.value == "OTHER":
                self._logger.info(
                    "other_assignment_reason",
                    run_id=run_id,
                    symbol=item.symbol,
                    reason=item.reason or "no_taxonomy_or_keyword_match",
                )
            if item.matched_existing:
                self._logger.info(
                    "taxonomy_match",
                    run_id=run_id,
                    symbol=item.symbol,
                    catalyst_type=item.primary_catalyst_type.value,
                )
            elif item.proposed_catalyst_code:
                self._logger.info(
                    "taxonomy_fallback",
                    run_id=run_id,
                    symbol=item.symbol,
                    proposed_code=item.proposed_catalyst_code,
                )

        audit = load_from_state(state)
        classified_symbols = {item.symbol for item in enriched}
        for stock in state["identified_stocks"]:
            if stock.symbol in classified_symbols:
                record_stage(
                    audit,
                    symbol=stock.symbol,
                    stage=CATALYST_CLASSIFICATION,
                    input_values={"catalyst_type": next(
                        (s.primary_catalyst_type.value for s in enriched if s.symbol == stock.symbol),
                        None,
                    )},
                    passed=True,
                    run_id=run_id,
                )
            else:
                record_stage(
                    audit,
                    symbol=stock.symbol,
                    stage=CATALYST_CLASSIFICATION,
                    passed=False,
                    rejection_reason=MISSING_CATALYST_DATA,
                    rejection_details={"missing_fields": ["catalyst_score", "sentiment"]},
                    run_id=run_id,
                )
        persist_to_state(state, audit)
        return state


class AssessCatalystImpactNode:
    """Assesses impact dimensions before quality scoring (no category rejection)."""

    name = "assess_catalyst_impact"

    def __init__(
        self,
        impact_service: CatalystImpactAssessmentService,
    ) -> None:
        self._impact = impact_service
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def execute(self, state: TradingState) -> TradingState:
        if not state["sentiment_results"]:
            state["tradable_catalyst_count"] = 0
            state["non_tradable_catalyst_count"] = 0
            state["tradability_rejections"] = []
            state["accepted_catalyst_diagnostics"] = []
            state["classified_count"] = 0
            return state

        assessed = []

        for sentiment in state["sentiment_results"]:
            updated = await self._impact.assess(sentiment, state["articles"])
            assessed.append(updated)

        state["sentiment_results"] = assessed
        state["tradable_catalyst_count"] = len(assessed)
        state["non_tradable_catalyst_count"] = 0
        state["tradability_rejections"] = []
        state["accepted_catalyst_diagnostics"] = []
        state["classified_count"] = len(assessed)
        self._logger.info(
            "assess_catalyst_impact_complete",
            assessed=len(assessed),
        )
        return state


# Backward-compatible alias for tests referencing the old node name.
AssessCatalystTradabilityNode = AssessCatalystImpactNode


class EnrichCatalystQualityNode:
    """Enriches sentiments with magnitude, materiality, and tradability scores."""

    name = "enrich_catalyst_quality"

    def __init__(self, enrichment_service: CatalystQualityEnrichmentService) -> None:
        self._enrichment = enrichment_service
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def execute(self, state: TradingState) -> TradingState:
        if not state["sentiment_results"]:
            return state
        llm_magnitudes = {
            s.symbol: s.llm_catalyst_magnitude
            for s in state["sentiment_results"]
            if s.llm_catalyst_magnitude is not None
        }
        llm_values = {
            s.symbol: s.llm_estimated_value_crore
            for s in state["sentiment_results"]
            if s.llm_estimated_value_crore is not None
        }
        llm_importance = {
            s.symbol: s.llm_strategic_importance
            for s in state["sentiment_results"]
            if s.llm_strategic_importance
        }
        enriched = self._enrichment.enrich(
            state["sentiment_results"],
            state["articles"],
            llm_magnitudes=llm_magnitudes,
            llm_values_crore=llm_values,
            llm_strategic_importance=llm_importance,
        )
        enriched_map = {item.symbol: item for item in enriched}
        merged = [
            enriched_map.get(sentiment.symbol, sentiment)
            for sentiment in state["sentiment_results"]
        ]
        state["sentiment_results"] = merged
        state["accepted_catalyst_diagnostics"] = [
            AcceptedCatalystDiagnostic(
                symbol=s.symbol,
                catalyst_type=s.primary_catalyst_type.value,
                tradability_score=s.catalyst_quality.tradability_score,
            )
            for s in merged
            if s.catalyst_quality is not None
        ]
        self._logger.info(
            "enrich_catalyst_quality_complete",
            count=len(enriched),
            sample=[
                {
                    "symbol": s.symbol,
                    "magnitude": s.catalyst_quality.magnitude.value if s.catalyst_quality else None,
                    "tradability": s.catalyst_quality.tradability_score if s.catalyst_quality else None,
                }
                for s in merged[:5]
            ],
        )
        return state


class TechnicalAnalysisNode:
    """Runs deterministic pre-market technical analysis."""

    name = "technical_analysis"

    def __init__(self, service: TechnicalAnalysisService) -> None:
        self._service = service
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def execute(self, state: TradingState) -> TradingState:
        if state.get("sentiment_results"):
            sentiment_symbols = {sentiment.symbol for sentiment in state["sentiment_results"]}
            stocks = [
                stock
                for stock in state["identified_stocks"]
                if stock.symbol in sentiment_symbols
            ]
        else:
            stocks = list(state["identified_stocks"])
        skipped = len(state["identified_stocks"]) - len(stocks)
        results = await self._service.analyze(stocks)
        distribution = self._service.technical_score_distribution(results)
        self._logger.info(
            "technical_analysis_complete",
            count=len(results),
            skipped_tradability=skipped,
            technical_score_distribution=distribution,
        )
        state["technical_results"] = results
        state["skipped_technical_count"] = skipped

        audit = load_from_state(state)
        run_id = state.get("run_id", "")
        analyzed_symbols = {r.symbol for r in results}
        for stock in stocks:
            if stock.symbol in analyzed_symbols:
                tech = next(r for r in results if r.symbol == stock.symbol)
                record_stage(
                    audit,
                    symbol=stock.symbol,
                    stage=TECHNICAL_ANALYSIS,
                    input_values={"technical_score": tech.technical_score},
                    passed=True,
                    run_id=run_id,
                )
            else:
                record_stage(
                    audit,
                    symbol=stock.symbol,
                    stage=TECHNICAL_ANALYSIS,
                    passed=False,
                    rejection_reason=MISSING_TECHNICAL_DATA,
                    rejection_details={"missing_fields": ["technical_score"]},
                    run_id=run_id,
                )
        persist_to_state(state, audit)
        return state


class BuildCandidatesNode:
    """Builds scored candidates for all joinable stocks (no truncation)."""

    name = "build_candidates"

    def __init__(
        self,
        strategy: RankingStrategy,
        audit_service: RankingPipelineAuditService | None = None,
    ) -> None:
        self._strategy = strategy
        self._audit = audit_service or RankingPipelineAuditService()
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def execute(self, state: TradingState) -> TradingState:
        traces = self._audit.build_initial_traces(state["identified_stocks"])
        symbol_weights = {
            m.symbol: m.beneficiary_weight
            for m in state.get("stock_mentions", [])
            if m.beneficiary_rank == 1
        }
        symbol_events = {
            b.symbol: e.event_id
            for e in state.get("event_records", [])
            for b in e.beneficiaries
        }
        if isinstance(self._strategy, InstitutionalRankingStrategyV4):
            self._strategy.set_market_features(
                MarketContextAgent().analyze(state.get("articles", []))
            )
        if isinstance(self._strategy, InstitutionalRankingStrategy):
            build_result = self._strategy.build_candidates(
                state["identified_stocks"],
                state["sentiment_results"],
                state["technical_results"],
                symbol_weights=symbol_weights,
                symbol_events=symbol_events,
            )
        else:
            build_result = self._strategy.build_candidates(
                state["identified_stocks"],
                state["sentiment_results"],
                state["technical_results"],
            )
        self._audit.apply_build_result(
            traces,
            build_result,
            sentiments=state["sentiment_results"],
        )
        dropped_count = (
            len(build_result.dropped_missing_sentiment)
            + len(build_result.dropped_missing_technical)
        )
        state["all_candidates"] = build_result.candidates
        state["pipeline_traces"] = list(traces.values())
        state["candidate_audits"] = self._audit.audit_service.to_state_list()
        state["dropped_missing_analysis_count"] = dropped_count
        state["dropped_tradability_count"] = len(build_result.dropped_tradability)
        self._logger.info(
            "build_candidates_complete",
            built=len(build_result.candidates),
            dropped_missing_sentiment=len(build_result.dropped_missing_sentiment),
            dropped_missing_technical=len(build_result.dropped_missing_technical),
            dropped_tradability=len(build_result.dropped_tradability),
        )
        return state


class FilterWatchlistNode:
    """Applies adaptive impact thresholds after ranking (rank-then-select)."""

    name = "filter_watchlist"

    def __init__(
        self,
        adaptive_filter: AdaptiveImpactFilterService,
        settings: ApplicationSettings,
        audit_service: RankingPipelineAuditService | None = None,
        near_miss_service: NearMissReviewService | None = None,
        event_beneficiary: EventBeneficiaryService | None = None,
        *,
        trading_profile: TradingProfileConfig | None = None,
        stats_service: CatalystTypeStatsService | None = None,
    ) -> None:
        self._adaptive_filter = adaptive_filter
        self._settings = settings
        self._profile = trading_profile or TradingProfileConfig.for_profile("swing")
        self._stats = stats_service
        self._audit = audit_service or RankingPipelineAuditService()
        self._near_miss = near_miss_service or NearMissReviewService()
        self._event_beneficiary = event_beneficiary or EventBeneficiaryService()
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def execute(self, state: TradingState) -> TradingState:
        pool = state["ranked_candidates"]
        filter_result = self._adaptive_filter.filter_with_result(
            pool,
            min_watchlist_size=self._settings.min_watchlist_size,
        )
        state["relaxation_pass_used"] = filter_result.relaxation_pass_used
        state["gate_min_freshness_override"] = filter_result.gate_min_freshness_override
        state["adaptive_threshold_snapshot"] = filter_result.adaptive_threshold_snapshot
        state["penalty_counts"] = filter_result.penalty_counts
        state["hard_reject_count"] = len(filter_result.rejected)

        if not self._profile.use_penalty_framework:
            event_accepted, event_rejected = self._event_beneficiary.apply_event_caps(
                filter_result.accepted,
                state.get("event_records", []),
            )
            filter_result.accepted = event_accepted
            filter_result.rejected.extend(event_rejected)

        if self._stats is not None:
            await self._record_stats(filter_result)

        traces = {t.symbol: t for t in state["pipeline_traces"]}
        self._audit.apply_filter_result(
            traces,
            filter_result,
            adaptive_snapshot=filter_result.adaptive_threshold_snapshot,
        )
        state["pipeline_traces"] = list(traces.values())
        state["candidate_audits"] = self._audit.audit_service.to_state_list()
        state["filtered_candidates"] = filter_result.accepted
        state["rejected_candidates"] = filter_result.rejected
        state["near_miss_candidates"] = self._near_miss.review(filter_result.rejected)
        state["filter_rejection_counts"] = filter_result.rejection_counts
        state["passed_technical_filters"] = len(filter_result.accepted)

        min_size = self._settings.min_watchlist_size
        if len(filter_result.accepted) < min_size:
            self._logger.warning(
                "watchlist_below_min_size",
                accepted=len(filter_result.accepted),
                min_watchlist_size=min_size,
                rejected=len(filter_result.rejected),
            )

        self._logger.info(
            "watchlist_filter_complete",
            input_candidates=len(state["all_candidates"]),
            accepted=len(filter_result.accepted),
            rejected=len(filter_result.rejected),
            rejection_counts=filter_result.rejection_counts,
            relaxation_pass_used=state.get("relaxation_pass_used", "none"),
            adaptive_thresholds=filter_result.adaptive_threshold_snapshot,
            rejected_symbols=[c.stock.symbol for c in filter_result.rejected],
        )
        return state

    async def _record_stats(self, filter_result) -> None:
        for candidate in filter_result.accepted:
            code = candidate.sentiment.primary_catalyst_type.value
            impact = candidate.sentiment.catalyst_impact
            await self._stats.record_outcome(
                code,
                accepted=True,
                composite_score=candidate.composite_impact_score or 0.0,
                tradability=impact.tradability if impact else 50.0,
            )
        for candidate in filter_result.rejected:
            code = candidate.sentiment.primary_catalyst_type.value
            impact = candidate.sentiment.catalyst_impact
            await self._stats.record_outcome(
                code,
                accepted=False,
                composite_score=candidate.composite_impact_score or 0.0,
                tradability=impact.tradability if impact else 50.0,
            )


class ValidateScoresNode:
    """Validates candidate scores before ranking."""

    name = "validate_scores"

    def __init__(
        self,
        validator: ScoreValidator | None = None,
        audit_service: RankingPipelineAuditService | None = None,
    ) -> None:
        self._validator = validator or ScoreValidator()
        self._audit = audit_service or RankingPipelineAuditService()
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def execute(self, state: TradingState) -> TradingState:
        candidates = state["all_candidates"]
        result = self._validator.validate(candidates)
        run_id = state.get("run_id", "")
        audit = self._audit.audit_service

        for candidate in result.rejected:
            symbol = candidate.stock.symbol
            reason = result.rejection_reasons.get(symbol, "score_invalid")
            details = result.rejection_details.get(symbol, {})
            record_stage(
                audit,
                symbol=symbol,
                stage=SCORE_VALIDATION,
                input_values={"invalid_fields": details.get("invalid_fields", [])},
                passed=False,
                rejection_reason=reason,
                rejection_details=details,
                run_id=run_id,
            )

        for candidate in result.accepted:
            record_stage(
                audit,
                symbol=candidate.stock.symbol,
                stage=SCORE_VALIDATION,
                input_values={"final_score": candidate.final_score},
                passed=True,
                run_id=run_id,
            )

        state["all_candidates"] = result.accepted
        state["score_validation_rejection_count"] = len(result.rejected)
        persist_to_state(state, audit)
        self._logger.info(
            "validate_scores_complete",
            accepted=len(result.accepted),
            rejected=len(result.rejected),
        )
        return state


class RankingNode:
    """Sorts filtered candidates by final score (no truncation)."""

    name = "ranking"

    def __init__(
        self,
        strategy: RankingStrategy,
        explanation_builder: CandidateExplanationBuilder | None = None,
        audit_service: RankingPipelineAuditService | None = None,
    ) -> None:
        self._strategy = strategy
        self._explanation_builder = explanation_builder or CandidateExplanationBuilder()
        self._audit = audit_service or RankingPipelineAuditService()
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def execute(self, state: TradingState) -> TradingState:
        ranked = self._strategy.sort_candidates(state["all_candidates"])
        distribution = self._ranking_distribution(ranked)
        run_id = state.get("run_id", "")
        audit = load_from_state(state)
        for candidate in ranked:
            record_stage(
                audit,
                symbol=candidate.stock.symbol,
                stage=RANKING,
                input_values={"final_score": candidate.final_score},
                passed=True,
                run_id=run_id,
            )
        persist_to_state(state, audit)
        for candidate in ranked[:5]:
            self._logger.info(
                "ranking_explanation",
                **self._explanation_builder.ranking_explanation_dict(candidate),
            )
        self._logger.info(
            "ranking_complete",
            candidate_count=len(ranked),
            final_ranking_distribution=distribution,
        )
        state["sorted_candidates"] = ranked
        state["ranked_candidates"] = ranked
        return state

    @staticmethod
    def _ranking_distribution(candidates) -> dict[str, int]:
        buckets = {"0-60": 0, "60-75": 0, "75-85": 0, "85-100": 0}
        for candidate in candidates:
            score = candidate_final_score(candidate)
            if score < 60:
                buckets["0-60"] += 1
            elif score < 75:
                buckets["60-75"] += 1
            elif score < 85:
                buckets["75-85"] += 1
            else:
                buckets["85-100"] += 1
        return buckets


class ProfessionalTraderGateNode:
    """Professional trader validation on filtered survivors."""

    name = "professional_trader_gate"

    def __init__(
        self,
        gate: ProfessionalTraderGateService,
        settings: ApplicationSettings,
        audit_service: RankingPipelineAuditService | None = None,
    ) -> None:
        self._gate = gate
        self._settings = settings
        self._audit = audit_service or RankingPipelineAuditService()
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def execute(self, state: TradingState) -> TradingState:
        pool = state["filtered_candidates"]
        gate = self._gate
        freshness_override = state.get("gate_min_freshness_override")
        if freshness_override is not None:
            gate = ProfessionalTraderGateService(
                config=self._gate.config.model_copy(
                    update={"min_freshness": freshness_override}
                )
            )
        result = gate.filter_with_relaxation(
            pool,
            min_size=self._settings.min_watchlist_size,
            allow_relaxation=self._settings.watchlist_allow_relaxation,
            step=self._settings.watchlist_relaxation_step,
        )
        if result.relaxation_applied and state.get("relaxation_pass_used", "none") == "none":
            state["relaxation_pass_used"] = "gate_relaxation"
        if result.fallback_applied:
            state["relaxation_pass_used"] = "gate_fallback"

        gate_rejection_reasons: dict[str, list[str]] = {}
        for candidate in result.rejected:
            evaluation = gate.evaluate_with_reasons(candidate)
            gate_rejection_reasons[candidate.stock.symbol] = list(
                evaluation.rejection_reasons
            )

        traces = {t.symbol: t for t in state.get("pipeline_traces", [])}
        self._audit.apply_gate_result(
            traces,
            accepted=result.accepted,
            rejected=result.rejected,
            rejection_reasons=gate_rejection_reasons,
        )
        state["pipeline_traces"] = list(traces.values())
        state["candidate_audits"] = self._audit.audit_service.to_state_list()
        state["filtered_candidates"] = result.accepted
        state["rejected_candidates"] = list(state.get("rejected_candidates", [])) + result.rejected
        self._logger.info(
            "professional_trader_gate_complete",
            accepted=len(result.accepted),
            rejected=len(result.rejected),
            relaxation_applied=result.relaxation_applied,
            fallback_applied=result.fallback_applied,
            input_count=len(pool),
        )
        return state


class PipelineMetricsNode:
    """Emits institutional pipeline monitoring metrics."""

    name = "pipeline_metrics"

    def __init__(self, metrics: PipelineMetricsService) -> None:
        self._metrics = metrics

    async def execute(self, state: TradingState) -> TradingState:
        self._metrics.emit_run_summary(state)
        return state


class SelectWatchlistNode:
    """Tiered selection with directional buckets and max cap."""

    name = "select_watchlist"

    def __init__(
        self,
        settings: ApplicationSettings,
        audit_service: RankingPipelineAuditService | None = None,
        *,
        tiered_selector: TieredWatchlistSelector | None = None,
        trading_profile: TradingProfileConfig | None = None,
    ) -> None:
        self._settings = settings
        self._profile = trading_profile or TradingProfileConfig.for_profile("swing")
        self._tiered = tiered_selector
        self._audit = audit_service or RankingPipelineAuditService()
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def execute(self, state: TradingState) -> TradingState:
        max_size = self._settings.max_watchlist_size
        min_size = self._settings.min_watchlist_size
        pool = state["filtered_candidates"]
        survivors_before_cap = len(pool)

        select_drops: list = []
        if self._profile.use_penalty_framework and self._tiered:
            selection = self._tiered.select(
                pool,
                min_size=min_size,
                max_size=max_size,
                event_records=state.get("event_records"),
            )
            watchlist = selection.selected
            select_drops = selection.dropped
            state["long_candidates"] = selection.long_candidates
            state["short_candidates"] = selection.short_candidates
            state["neutral_candidates"] = selection.neutral_candidates
            state["tier_fill_counts"] = selection.tier_counts
        else:
            watchlist = pool[:max_size]
            state["long_candidates"] = watchlist
            state["short_candidates"] = []
            state["neutral_candidates"] = []
            state["tier_fill_counts"] = {}

        drop_counts: dict[str, int] = {}
        for drop in select_drops:
            drop_counts[drop.reason] = drop_counts.get(drop.reason, 0) + 1
        state["select_drop_counts"] = drop_counts

        mismatch_count = 0
        for candidate in pool:
            payload = tradability_shadow_payload(candidate)
            gate = payload["gate_tradability"]
            quality = payload["quality_tradability"]
            if gate is not None and quality is not None and gate != quality:
                mismatch_count += 1
        self._logger.info(
            "watchlist_tradability_shadow_summary",
            candidates=len(pool),
            gate_quality_mismatch_count=mismatch_count,
        )

        traces = {t.symbol: t for t in state["pipeline_traces"]}
        self._audit.apply_select_result(
            traces, selected=watchlist, drops=select_drops
        )
        state["pipeline_traces"] = list(traces.values())
        state["candidate_audits"] = self._audit.audit_service.to_state_list()
        state["ranked_candidates"] = watchlist
        if survivors_before_cap > 0 and len(watchlist) == 0:
            self._logger.warning(
                "select_watchlist_empty_fallback",
                survivors_before_cap=survivors_before_cap,
                max_watchlist_size=max_size,
            )
            watchlist = sorted(pool, key=candidate_adjusted_score, reverse=True)[:max_size]
            state["ranked_candidates"] = watchlist
            state["long_candidates"] = watchlist
        self._logger.info(
            "select_watchlist_complete",
            survivors_before_cap=survivors_before_cap,
            final_watchlist_size=len(watchlist),
            long=len(state.get("long_candidates", [])),
            short=len(state.get("short_candidates", [])),
            neutral=len(state.get("neutral_candidates", [])),
            tier_fill=state.get("tier_fill_counts"),
            dropped_by_reason=drop_counts,
        )
        return state


class PipelineConsistencyNode:
    """Validates watchlist size never exceeds filter survivors."""

    name = "pipeline_consistency"

    def __init__(self, settings: ApplicationSettings) -> None:
        self._settings = settings
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def execute(self, state: TradingState) -> TradingState:
        filtered = state["filtered_candidates"]
        watchlist = state["ranked_candidates"]
        max_size = self._settings.max_watchlist_size

        if len(watchlist) > len(filtered):
            msg = (
                f"pipeline_consistency_violation: watchlist {len(watchlist)} > "
                f"survivors {len(filtered)}"
            )
            state["errors"].append(msg)
            self._logger.error("pipeline_consistency_violation", watchlist=len(watchlist), survivors=len(filtered))

        if len(watchlist) > max_size:
            msg = (
                f"pipeline_consistency_violation: watchlist {len(watchlist)} > "
                f"max_watchlist_size {max_size}"
            )
            state["errors"].append(msg)
            self._logger.error(
                "pipeline_consistency_violation",
                watchlist=len(watchlist),
                max_watchlist_size=max_size,
            )

        rejected_symbols = {
            c.stock.symbol for c in state.get("rejected_candidates", [])
        }
        watchlist_symbols = {c.stock.symbol for c in watchlist}
        overlap = rejected_symbols & watchlist_symbols
        if overlap:
            msg = f"pipeline_consistency_violation: rejected symbols in watchlist: {sorted(overlap)}"
            state["errors"].append(msg)
            self._logger.error("pipeline_consistency_violation", overlap=sorted(overlap))

        long_pool = state.get("long_candidates", [])
        short_pool = state.get("short_candidates", [])
        neutral_pool = state.get("neutral_candidates", [])
        if long_pool or short_pool or neutral_pool:
            directional_total = len(long_pool) + len(short_pool) + len(neutral_pool)
            if len(watchlist) != directional_total:
                msg = (
                    f"pipeline_consistency_violation: watchlist {len(watchlist)} != "
                    f"directional pools {directional_total}"
                )
                state["errors"].append(msg)
                self._logger.error(
                    "pipeline_consistency_violation",
                    watchlist=len(watchlist),
                    directional_total=directional_total,
                )

        return state


class ExplainCandidatesNode:
    """Builds explainability metadata for ranked candidates."""

    name = "explain_candidates"

    def __init__(
        self,
        explanation_builder: CandidateExplanationBuilder | None = None,
    ) -> None:
        self._explanation_builder = explanation_builder or CandidateExplanationBuilder()

    async def execute(self, state: TradingState) -> TradingState:
        state["ranked_candidates"] = [
            self._explanation_builder.enrich(candidate)
            for candidate in state["ranked_candidates"]
        ]
        return state


class GenerateWatchlistNode:
    """Generates watchlist and markdown report."""

    name = "generate_watchlist"

    def __init__(
        self,
        builder: WatchlistReportBuilder,
        llm: LLMProvider,
        settings: ApplicationSettings,
        *,
        effective_strategy: str,
        detected_session: TradingSessionMode,
    ) -> None:
        self._builder = builder
        self._llm = llm
        self._settings = settings
        self._effective_strategy = effective_strategy
        self._detected_session = detected_session

    async def execute(self, state: TradingState) -> TradingState:
        run_datetime = datetime.combine(state["run_date"], datetime.min.time(), tzinfo=UTC)
        watchlist = self._builder.build_watchlist(
            state["ranked_candidates"],
            run_date=run_datetime,
            strategy=self._effective_strategy,
            session_mode=self._detected_session,
        )
        state["watchlist"] = watchlist

        if self._settings.template_report_first:
            report = self._builder.build_fallback_report(
                watchlist,
                state["ranked_candidates"],
                session=self._detected_session,
                long_candidates=state.get("long_candidates"),
                short_candidates=state.get("short_candidates"),
                neutral_candidates=state.get("neutral_candidates"),
            )
            report.metadata["report_mode"] = "template_primary"
        else:
            try:
                markdown = await self._llm.generate_report(watchlist, state["ranked_candidates"])
                report = DailyReport(
                    run_date=run_datetime,
                    markdown=markdown,
                    watchlist_id=watchlist.id,
                    metadata={
                        "strategy": self._effective_strategy,
                        "llm_provider": self._llm.provider_name,
                    },
                )
            except Exception as exc:
                if state["dry_run"] or is_quota_exhausted_error(exc):
                    report = self._builder.build_fallback_report(
                        watchlist,
                        state["ranked_candidates"],
                        session=self._detected_session,
                        long_candidates=state.get("long_candidates"),
                        short_candidates=state.get("short_candidates"),
                        neutral_candidates=state.get("neutral_candidates"),
                    )
                    if not state["dry_run"]:
                        report.metadata["llm_provider"] = self._llm.provider_name
                        report.metadata["llm_fallback_reason"] = "gemini_quota_exhausted"
                else:
                    raise LLMException(
                        f"Gemini report generation failed: {exc}", cause=exc
                    ) from exc

        state["report"] = report
        return state


class PersistResultsNode:
    """Persists all results to PostgreSQL when enabled."""

    name = "persist_results"

    def __init__(
        self,
        article_repo: ArticleRepository,
        analysis_repo: AnalysisRepository,
        watchlist_repo: WatchlistRepository,
        ranking_audit_repo: RankingAuditRepository,
        recommendation_persistence: RecommendationPersistenceService,
        *,
        enabled: bool = True,
        persist_all_filtered: bool = False,
    ) -> None:
        self._article_repo = article_repo
        self._analysis_repo = analysis_repo
        self._watchlist_repo = watchlist_repo
        self._ranking_audit_repo = ranking_audit_repo
        self._recommendation_persistence = recommendation_persistence
        self._enabled = enabled
        self._persist_all_filtered = persist_all_filtered
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def execute(self, state: TradingState) -> TradingState:
        if state["dry_run"] or not self._enabled:
            self._logger.info("persist_skipped", enabled=self._enabled)
            return state

        run_datetime = datetime.combine(state["run_date"], datetime.min.time(), tzinfo=UTC)
        if state["articles"]:
            await self._article_repo.save_batch(state["articles"], run_date=run_datetime)
        if state["sentiment_results"]:
            await self._analysis_repo.save_sentiment(
                state["sentiment_results"], run_date=run_datetime
            )
        if state["technical_results"]:
            await self._analysis_repo.save_technical_results(
                state["technical_results"], run_date=run_datetime
            )
        audit_source = (
            state["filtered_candidates"]
            if self._persist_all_filtered
            else state["ranked_candidates"]
        )
        if audit_source:
            audit_records = RankingAuditBuilder.build(audit_source, run_date=run_datetime)
            await self._ranking_audit_repo.save_batch(audit_records, run_date=run_datetime)
        if state["watchlist"]:
            await self._watchlist_repo.save_watchlist(state["watchlist"])
            await self._recommendation_persistence.save_from_watchlist(
                state["watchlist"],
                state["ranked_candidates"],
                trade_date=state["run_date"],
            )
        if state["report"]:
            await self._watchlist_repo.save_daily_report(state["report"])
        self._logger.info("persist_complete")
        return state


class SendTelegramNode:
    """Sends the final report via Telegram when enabled."""

    name = "send_telegram"

    def __init__(self, notifier: NotificationProvider, *, enabled: bool = True) -> None:
        self._notifier = notifier
        self._enabled = enabled
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def execute(self, state: TradingState) -> TradingState:
        if state["dry_run"] or not self._enabled or state["report"] is None:
            self._logger.info("telegram_skipped", enabled=self._enabled)
            return state
        await self._notifier.send_message(state["report"].markdown)
        self._logger.info("telegram_sent")
        return state
