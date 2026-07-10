"""Maps LLM sentiment DTOs to domain SentimentAnalysis."""

from uuid import UUID

from morning_trading_agent.application.services.catalyst.catalyst_scoring_service import (
    CatalystScoringService,
)
from morning_trading_agent.domain.entities.article import SentimentAnalysis
from morning_trading_agent.domain.entities.llm_sentiment import LLMSentimentAnalysis
from morning_trading_agent.domain.value_objects.catalyst_mapper import CatalystTypeMapper
from morning_trading_agent.domain.value_objects.sentiment import SentimentDirection


class SentimentAnalysisMapper:
    """Converts LLM output to domain sentiment with deterministic catalyst scores."""

    def __init__(self, *, scoring_service: CatalystScoringService) -> None:
        self._scoring = scoring_service

    def to_domain(
        self,
        llm: LLMSentimentAnalysis,
        *,
        catalyst_code: str | None = None,
    ) -> SentimentAnalysis:
        raw_type = catalyst_code or llm.catalyst_code or llm.catalyst_type
        catalyst_type = CatalystTypeMapper.from_value(raw_type)
        direction = llm.direction
        if isinstance(direction, str):
            direction = SentimentDirection(direction.lower())

        catalyst_score = self._scoring.score_with_direct_news_cap(
            catalyst_type,
            direct_company_news=llm.direct_company_news,
            direction=direction,
        )

        article_ids: list[UUID] = []
        for raw_id in llm.article_ids:
            try:
                article_ids.append(UUID(str(raw_id)))
            except ValueError:
                continue

        return SentimentAnalysis(
            symbol=llm.symbol,
            score=max(-10.0, min(10.0, llm.score)),
            confidence=max(0.0, min(1.0, llm.confidence)),
            direction=direction,
            reason=llm.reason,
            article_ids=article_ids,
            catalyst_score=catalyst_score,
            primary_catalyst_type=catalyst_type,
            primary_catalyst_summary=llm.reason[:200],
            direct_company_news=llm.direct_company_news,
            classification_confidence=llm.classification_confidence,
            matched_existing=llm.matched_existing,
            proposed_catalyst_code=llm.proposed_code,
            llm_classified=True,
            catalyst_impact=llm.impact,
            llm_catalyst_magnitude=llm.catalyst_magnitude,
            llm_estimated_value_crore=llm.estimated_value_crore,
            llm_strategic_importance=llm.strategic_importance,
        )
