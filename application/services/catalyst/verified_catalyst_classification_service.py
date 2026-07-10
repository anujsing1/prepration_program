"""Catalyst classification with optional verification agent."""

from morning_trading_agent.agents.catalyst.catalyst_verification_agent import (
    CatalystVerificationAgent,
)
from morning_trading_agent.application.services.catalyst.catalyst_classification_service import (
    CatalystClassificationService,
)
from morning_trading_agent.domain.entities.article import Article, SentimentAnalysis
from morning_trading_agent.domain.entities.llm_sentiment import LLMSentimentAnalysis


class VerifiedCatalystClassificationService(CatalystClassificationService):
    """Wraps classification with optional post-verify agent pass."""

    def __init__(
        self,
        *,
        base: CatalystClassificationService,
        verifier: CatalystVerificationAgent | None = None,
    ) -> None:
        super().__init__(
            scoring_service=base._scoring,
            mapper=base._mapper,
            enricher=base._enricher,
            headline_refinement=base._headline_refinement,
            hybrid_classifier=base._hybrid,
            taxonomy_discovery=base._taxonomy_discovery,
            taxonomy_cache=base._taxonomy_cache,
            reclassification_service=base._reclassification,
            use_db_taxonomy=base._use_db_taxonomy,
        )
        self._verifier = verifier

    async def classify_from_llm_async(
        self, llm_results: list[LLMSentimentAnalysis], articles: list[Article]
    ) -> list[SentimentAnalysis]:
        results = await super().classify_from_llm_async(llm_results, articles)
        if self._verifier is None:
            return results
        return self._verifier.verify(results, articles)

    def classify_from_llm(
        self, llm_results: list[LLMSentimentAnalysis], articles: list[Article]
    ) -> list[SentimentAnalysis]:
        results = super().classify_from_llm(llm_results, articles)
        if self._verifier is None:
            return results
        return self._verifier.verify(results, articles)

    def classify(
        self, results: list[SentimentAnalysis], articles: list[Article]
    ) -> list[SentimentAnalysis]:
        classified = super().classify(results, articles)
        if self._verifier is None:
            return classified
        return self._verifier.verify(classified, articles)
