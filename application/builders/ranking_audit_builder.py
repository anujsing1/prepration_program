"""Builds ranking audit records from ranked candidates."""

from datetime import datetime

from morning_trading_agent.domain.entities.article import TradingCandidate
from morning_trading_agent.domain.entities.explanation import ScoreBreakdown
from morning_trading_agent.domain.entities.ranking_audit import RankingAuditRecord


class RankingAuditBuilder:
    """Maps ranked candidates to persistence-ready audit records."""

    @staticmethod
    def build(records: list[TradingCandidate], *, run_date: datetime) -> list[RankingAuditRecord]:
        audit_records: list[RankingAuditRecord] = []
        for candidate in records:
            quality = candidate.sentiment.catalyst_quality
            breakdown = candidate.score_breakdown or ScoreBreakdown(
                technical=candidate.technical_score,
                catalyst=candidate.effective_catalyst_score or candidate.catalyst_score,
                sentiment=candidate.news_score,
                confidence=candidate.confidence_score,
                magnitude=candidate.magnitude_score or 0.0,
                materiality=candidate.materiality_score or 0.0,
                tradability=candidate.tradability_score or 0.0,
                final=candidate.final_score,
            )
            audit_records.append(
                RankingAuditRecord(
                    run_date=run_date,
                    symbol=candidate.stock.symbol,
                    catalyst_type=candidate.sentiment.primary_catalyst_type,
                    technical_score=candidate.technical_score,
                    catalyst_score=candidate.catalyst_score,
                    effective_catalyst_score=candidate.effective_catalyst_score,
                    catalyst_magnitude=quality.magnitude if quality else None,
                    magnitude_score=candidate.magnitude_score,
                    materiality_score=candidate.materiality_score,
                    tradability_score=candidate.tradability_score,
                    sentiment_score=candidate.news_score,
                    confidence_score=candidate.confidence_score,
                    freshness_score=candidate.freshness_score,
                    priority_score=candidate.priority_score,
                    final_score=candidate.final_score,
                    score_breakdown=breakdown,
                )
            )
        return audit_records
