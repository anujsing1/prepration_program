"""Orchestrates LLM catalyst classification with article keyword fallback."""

from __future__ import annotations

from collections import Counter

import structlog

from morning_trading_agent.application.services.catalyst.catalyst_headline_refinement_service import (
    CatalystHeadlineRefinementService,
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
from morning_trading_agent.application.services.catalyst.hybrid_catalyst_classifier import (
    HybridCatalystClassifier,
)
from morning_trading_agent.application.services.catalyst.sentiment_analysis_mapper import (
    SentimentAnalysisMapper,
)
from morning_trading_agent.application.services.news.sentiment_enricher import SentimentEnricher
from morning_trading_agent.domain.entities.article import Article, SentimentAnalysis
from morning_trading_agent.domain.entities.catalyst_taxonomy import (
    CatalystTaxonomyEntry,
    PendingCatalystSummary,
)
from morning_trading_agent.domain.entities.llm_sentiment import LLMSentimentAnalysis
from morning_trading_agent.domain.value_objects.catalyst import WEAK_CATALYST_TYPES, CatalystType

_EARNINGS_TYPES: frozenset[CatalystType] = frozenset(
    {
        CatalystType.EARNINGS,
        CatalystType.EARNINGS_BEAT,
        CatalystType.EARNINGS_MISS,
    }
)
_EARNINGS_KEYWORDS: tuple[str, ...] = (
    "results",
    "quarterly",
    "quarter",
    " q1",
    " q2",
    " q3",
    " q4",
    "profit",
    "revenue",
    "guidance",
    "ebitda",
    " pat ",
    "net profit",
)


class CatalystClassificationService:
    """Merges LLM catalyst fields with article metadata and deterministic scoring."""

    def __init__(
        self,
        *,
        scoring_service: CatalystScoringService | None = None,
        mapper: SentimentAnalysisMapper | None = None,
        enricher: SentimentEnricher | None = None,
        headline_refinement: CatalystHeadlineRefinementService | None = None,
        hybrid_classifier: HybridCatalystClassifier | None = None,
        taxonomy_discovery: CatalystTaxonomyDiscoveryService | None = None,
        taxonomy_cache: CatalystTaxonomyCache | None = None,
        reclassification_service: CatalystReclassificationService | None = None,
        use_db_taxonomy: bool = False,
    ) -> None:
        scoring = scoring_service or CatalystScoringService()
        self._scoring = scoring
        self._mapper = mapper or SentimentAnalysisMapper(scoring_service=scoring)
        self._enricher = enricher or SentimentEnricher()
        self._headline_refinement = headline_refinement or CatalystHeadlineRefinementService(
            scoring_service=scoring
        )
        self._hybrid = hybrid_classifier or HybridCatalystClassifier(
            scoring_service=scoring,
            headline_refinement=self._headline_refinement,
        )
        self._taxonomy_discovery = taxonomy_discovery
        self._taxonomy_cache = taxonomy_cache
        self._reclassification = reclassification_service
        self._use_db_taxonomy = use_db_taxonomy
        self._logger = structlog.get_logger(self.__class__.__name__)

    @property
    def use_db_taxonomy(self) -> bool:
        return self._use_db_taxonomy

    @property
    def pending_discoveries(self) -> list[PendingCatalystSummary]:
        if self._taxonomy_discovery is None:
            return []
        return self._taxonomy_discovery.run_discoveries

    def reset_pending_discoveries(self) -> None:
        if self._taxonomy_discovery is not None:
            self._taxonomy_discovery.reset_run_discoveries()

    async def load_taxonomy_entries(self) -> list[CatalystTaxonomyEntry] | None:
        if self._taxonomy_cache is None:
            return None
        return await self._taxonomy_cache.load()

    def classify_from_llm(
        self, llm_results: list[LLMSentimentAnalysis], articles: list[Article]
    ) -> list[SentimentAnalysis]:
        """Map LLM results, apply article fallback, enrich freshness/priority."""
        domain_results = [self._mapper.to_domain(item) for item in llm_results]
        return self._finalize(domain_results, articles)

    async def classify_from_llm_async(
        self, llm_results: list[LLMSentimentAnalysis], articles: list[Article]
    ) -> list[SentimentAnalysis]:
        """Map LLM results with taxonomy discovery when enabled."""
        if self._taxonomy_discovery is None:
            return self.classify_from_llm(llm_results, articles)

        self._taxonomy_discovery.reset_run_discoveries()
        domain_results: list[SentimentAnalysis] = []
        for llm in llm_results:
            headline = self._example_headline(llm, articles)
            outcome = await self._taxonomy_discovery.resolve(
                matched_existing=llm.matched_existing,
                catalyst_code=llm.catalyst_code or llm.catalyst_type,
                proposed_code=llm.proposed_code,
                proposed_name=llm.proposed_name,
                parent_category=llm.parent_category,
                description=llm.description,
                confidence=llm.classification_confidence,
                reason=llm.reason,
                symbol=llm.symbol,
                example_headline=headline,
            )
            domain_results.append(
                self._mapper.to_domain(llm, catalyst_code=outcome.catalyst_code)
            )
        refined = self._refine_results(domain_results, articles, skip_hybrid=self._use_db_taxonomy)
        if self._reclassification is not None:
            refined = await self._reclassification.reclassify(refined, articles)
        return self._enricher.enrich(refined, articles)

    def classify(
        self, results: list[SentimentAnalysis], articles: list[Article]
    ) -> list[SentimentAnalysis]:
        """Classify pre-built sentiment rows (non-LLM path / stub)."""
        return self._finalize(results, articles)

    def _example_headline(self, llm: LLMSentimentAnalysis, articles: list[Article]) -> str:
        article_map = {str(article.id): article for article in articles}
        for raw_id in llm.article_ids:
            article = article_map.get(str(raw_id))
            if article is not None:
                return article.title
        return llm.reason[:200]

    def _finalize(
        self,
        results: list[SentimentAnalysis],
        articles: list[Article],
        *,
        skip_hybrid: bool = False,
    ) -> list[SentimentAnalysis]:
        refined = self._refine_results(results, articles, skip_hybrid=skip_hybrid)
        return self._enricher.enrich(refined, articles)

    def _refine_results(
        self,
        results: list[SentimentAnalysis],
        articles: list[Article],
        *,
        skip_hybrid: bool = False,
    ) -> list[SentimentAnalysis]:
        article_map = {article.id: article for article in articles}
        merged = [
            self._validate_earnings_classification(
                self._apply_article_fallback(result, articles),
                articles,
            )
            for result in results
        ]
        if skip_hybrid:
            refined = [
                self._headline_refinement.refine(
                    sentiment,
                    [article_map[aid] for aid in sentiment.article_ids if aid in article_map],
                )
                if sentiment.primary_catalyst_type == CatalystType.OTHER
                and any(aid in article_map for aid in sentiment.article_ids)
                else sentiment
                for sentiment in merged
            ]
        else:
            refined = [self._hybrid.classify_sentiment(sentiment, articles) for sentiment in merged]
        other_count = sum(
            1 for s in refined if s.primary_catalyst_type == CatalystType.OTHER
        )
        self._logger.info(
            "classification_summary",
            total=len(refined),
            other_count=other_count,
            types=dict(Counter(s.primary_catalyst_type.value for s in refined)),
        )
        return refined

    def _validate_earnings_classification(
        self, result: SentimentAnalysis, articles: list[Article]
    ) -> SentimentAnalysis:
        if result.primary_catalyst_type not in _EARNINGS_TYPES:
            return result

        article_map = {article.id: article for article in articles}
        linked = [article_map[aid] for aid in result.article_ids if aid in article_map]
        text_parts = [
            result.primary_catalyst_summary,
            result.reason,
            *(article.title for article in linked),
            *(article.content[:500] for article in linked),
        ]
        combined = " ".join(part for part in text_parts if part).lower()
        if any(keyword in combined for keyword in _EARNINGS_KEYWORDS):
            return result

        original_type = result.primary_catalyst_type.value
        self._logger.info(
            "earnings_reclassified",
            symbol=result.symbol,
            original_type=original_type,
            reason="missing_earnings_keywords",
        )
        catalyst_score = self._scoring.score_with_direct_news_cap(
            CatalystType.OTHER,
            direct_company_news=False,
            direction=result.direction,
        )
        return result.model_copy(
            update={
                "primary_catalyst_type": CatalystType.OTHER,
                "direct_company_news": False,
                "catalyst_score": catalyst_score,
            }
        )

    def _apply_article_fallback(
        self, result: SentimentAnalysis, articles: list[Article]
    ) -> SentimentAnalysis:
        if self._use_db_taxonomy and result.llm_classified and result.matched_existing:
            return result

        article_map = {article.id: article for article in articles}
        linked = [article_map[aid] for aid in result.article_ids if aid in article_map]

        best_article = max(
            linked,
            key=lambda article: (article.catalyst_score, article.priority_score),
            default=None,
        )
        if not linked or best_article is None:
            return result

        catalyst_type = result.primary_catalyst_type
        direct_news = result.direct_company_news

        if not result.llm_classified or catalyst_type in {CatalystType.OTHER, CatalystType.GENERIC_MENTION}:
            if best_article.catalyst_type not in WEAK_CATALYST_TYPES:
                catalyst_type = best_article.catalyst_type
            elif result.llm_classified and catalyst_type in WEAK_CATALYST_TYPES:
                catalyst_type = result.primary_catalyst_type
            else:
                catalyst_type = best_article.catalyst_type

        if result.llm_classified and result.primary_catalyst_type in WEAK_CATALYST_TYPES:
            direct_news = False
        elif not result.llm_classified and best_article.catalyst_type in WEAK_CATALYST_TYPES:
            direct_news = False

        catalyst_score = self._scoring.score_with_direct_news_cap(
            catalyst_type,
            direct_company_news=direct_news,
            direction=result.direction,
        )

        summary = (
            best_article.catalyst_analysis.summary
            if best_article.catalyst_analysis
            else best_article.title[:200]
        )

        return result.model_copy(
            update={
                "primary_catalyst_type": catalyst_type,
                "catalyst_score": catalyst_score,
                "direct_company_news": direct_news,
                "primary_catalyst_summary": summary or result.reason,
            }
        )
