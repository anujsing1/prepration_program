"""Batch LLM reclassification for remaining OTHER catalyst types."""

from __future__ import annotations

import structlog

from morning_trading_agent.application.ports.providers import LLMProvider
from morning_trading_agent.application.services.catalyst.catalyst_headline_refinement_service import (
    CatalystHeadlineRefinementService,
)
from morning_trading_agent.application.services.catalyst.catalyst_scoring_service import (
    CatalystScoringService,
)
from morning_trading_agent.application.services.catalyst.catalyst_similarity import (
    find_best_match,
)
from morning_trading_agent.application.services.catalyst.catalyst_taxonomy_cache import (
    CatalystTaxonomyCache,
)
from morning_trading_agent.domain.entities.article import Article, SentimentAnalysis
from morning_trading_agent.domain.entities.llm_sentiment import CatalystReclassificationRequest
from morning_trading_agent.domain.value_objects.catalyst import CatalystType
from morning_trading_agent.domain.value_objects.catalyst_mapper import CatalystTypeMapper

_SIMILARITY_THRESHOLD = 0.85


class CatalystReclassificationService:
    """Resolves OTHER classifications via taxonomy lookup, semantic match, and LLM."""

    def __init__(
        self,
        *,
        llm: LLMProvider,
        taxonomy_cache: CatalystTaxonomyCache | None = None,
        scoring_service: CatalystScoringService | None = None,
        headline_refinement: CatalystHeadlineRefinementService | None = None,
        enabled: bool = True,
    ) -> None:
        self._llm = llm
        self._cache = taxonomy_cache
        self._scoring = scoring_service or CatalystScoringService()
        self._headline = headline_refinement or CatalystHeadlineRefinementService(
            scoring_service=self._scoring
        )
        self._enabled = enabled
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def reclassify(
        self,
        sentiments: list[SentimentAnalysis],
        articles: list[Article],
    ) -> list[SentimentAnalysis]:
        if not self._enabled or not sentiments:
            return sentiments

        article_map = {article.id: article for article in articles}
        updated: list[SentimentAnalysis] = []
        llm_batch: list[CatalystReclassificationRequest] = []
        llm_indices: list[int] = []

        for sentiment in sentiments:
            if sentiment.primary_catalyst_type != CatalystType.OTHER:
                updated.append(sentiment)
                continue

            linked = [article_map[aid] for aid in sentiment.article_ids if aid in article_map]
            resolved = self._resolve_other(sentiment, linked)
            if resolved.primary_catalyst_type != CatalystType.OTHER:
                updated.append(resolved)
                continue

            headline = linked[0].title if linked else sentiment.reason[:200]
            llm_indices.append(len(updated))
            updated.append(resolved)
            llm_batch.append(
                CatalystReclassificationRequest(
                    symbol=sentiment.symbol,
                    headline=headline,
                    summary=sentiment.primary_catalyst_summary or sentiment.reason,
                )
            )

        if not llm_batch:
            return updated

        taxonomy_codes = self._cache.codes() if self._cache is not None else []
        results = await self._llm.reclassify_catalysts(llm_batch, taxonomy_codes=taxonomy_codes)
        result_map = {item.symbol: item for item in results}

        for idx in llm_indices:
            sentiment = updated[idx]
            result = result_map.get(sentiment.symbol)
            if result is None or result.catalyst_code.upper() == CatalystType.OTHER.value:
                continue
            catalyst_type = CatalystTypeMapper.from_value(result.catalyst_code)
            if catalyst_type == CatalystType.OTHER:
                continue
            catalyst_score = self._scoring.score_with_direct_news_cap(
                catalyst_type,
                direct_company_news=sentiment.direct_company_news,
                direction=sentiment.direction,
            )
            self._logger.info(
                "catalyst_reclassified",
                symbol=sentiment.symbol,
                catalyst_code=catalyst_type.value,
                source="llm_batch",
            )
            updated[idx] = sentiment.model_copy(
                update={
                    "primary_catalyst_type": catalyst_type,
                    "catalyst_score": catalyst_score,
                    "matched_existing": result.matched_existing,
                    "llm_classified": True,
                    "classification_confidence": result.confidence,
                }
            )

        other_after = sum(1 for s in updated if s.primary_catalyst_type == CatalystType.OTHER)
        self._logger.info(
            "catalyst_reclassification_complete",
            other_before=sum(1 for s in sentiments if s.primary_catalyst_type == CatalystType.OTHER),
            other_after=other_after,
        )
        return updated

    def _resolve_other(
        self,
        sentiment: SentimentAnalysis,
        linked: list[Article],
    ) -> SentimentAnalysis:
        if self._cache is not None:
            proposed = sentiment.proposed_catalyst_code
            if proposed:
                entry = self._cache.get_by_code(proposed)
                if entry is not None:
                    catalyst_type = CatalystTypeMapper.from_value(entry.catalyst_code)
                    return self._apply_type(sentiment, catalyst_type, source="taxonomy_lookup")

            text = self._combined_text(sentiment, linked)
            candidates = [(code, "active") for code in self._cache.codes()]
            matches = find_best_match(text, candidates, threshold=_SIMILARITY_THRESHOLD)
            if matches:
                catalyst_type = CatalystTypeMapper.from_value(matches[0][0])
                if catalyst_type != CatalystType.OTHER:
                    return self._apply_type(
                        sentiment,
                        catalyst_type,
                        source=f"semantic_match:{matches[0][1]:.2f}",
                    )

        if linked:
            refined = self._headline.refine(sentiment, linked)
            if refined.primary_catalyst_type != CatalystType.OTHER:
                return refined
            return refined
        return sentiment

    def _apply_type(
        self,
        sentiment: SentimentAnalysis,
        catalyst_type: CatalystType,
        *,
        source: str,
    ) -> SentimentAnalysis:
        catalyst_score = self._scoring.score_with_direct_news_cap(
            catalyst_type,
            direct_company_news=sentiment.direct_company_news,
            direction=sentiment.direction,
        )
        self._logger.info(
            "catalyst_reclassified",
            symbol=sentiment.symbol,
            catalyst_code=catalyst_type.value,
            source=source,
        )
        return sentiment.model_copy(
            update={
                "primary_catalyst_type": catalyst_type,
                "catalyst_score": catalyst_score,
                "matched_existing": True,
                "llm_classified": True,
            }
        )

    @staticmethod
    def _combined_text(sentiment: SentimentAnalysis, articles: list[Article]) -> str:
        parts = [sentiment.primary_catalyst_summary, sentiment.reason]
        parts.extend(f"{article.title} {article.content[:300]}" for article in articles)
        return " ".join(part for part in parts if part)
