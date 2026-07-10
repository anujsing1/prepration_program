"""Impact dimension diagnostics for ranking and funnel reports."""

from __future__ import annotations

from morning_trading_agent.application.services.catalyst.candidate_impact_scoring_service import (
    CandidateImpactScoringService,
)
from morning_trading_agent.config.premarket_config import ImpactWeightConfig
from morning_trading_agent.domain.entities.article import TradingCandidate
from morning_trading_agent.domain.value_objects.catalyst_impact import CatalystImpactProfile


class ImpactDiagnosticsReportBuilder:
    """Builds why-high / why-rejected lines from impact dimensions."""

    def __init__(
        self,
        *,
        weight_config: ImpactWeightConfig | None = None,
        impact_scoring: CandidateImpactScoringService | None = None,
    ) -> None:
        self._scoring = impact_scoring or CandidateImpactScoringService(
            weight_config=weight_config
        )

    def why_scored_high(self, candidate: TradingCandidate) -> str:
        impact = candidate.sentiment.catalyst_impact or CatalystImpactProfile()
        composite = candidate.composite_impact_score or self._scoring.score_candidate(candidate)
        weights = (self._scoring._weights.normalized())  # noqa: SLF001
        top = impact.top_contributors(weights, limit=3)
        dims = " ".join(f"{name}={score:.0f}" for name, score in impact.dimension_items())
        drivers = ", ".join(f"{name} (+{value:.0f})" for name, value in top)
        catalyst = candidate.sentiment.primary_catalyst_type.value
        return (
            f"{candidate.stock.symbol} | composite={composite:.0f} | {dims} | "
            f"catalyst={catalyst} | Top drivers: {drivers}"
        )

    def why_rejected(self, candidate: TradingCandidate, reason: str) -> str:
        impact = candidate.sentiment.catalyst_impact or CatalystImpactProfile()
        composite = candidate.composite_impact_score or self._scoring.score_candidate(candidate)
        weakest = impact.weakest_dimensions(limit=2)
        weakest_text = ", ".join(f"{name}={score:.0f}" for name, score in weakest)
        return (
            f"{candidate.stock.symbol} | composite={composite:.0f} | reason={reason} | "
            f"weakest: {weakest_text}"
        )

    def lifecycle_rows(
        self,
        candidates: list[TradingCandidate],
        *,
        rejection_reasons: dict[str, str],
    ) -> list[dict[str, str | float | bool]]:
        rows: list[dict[str, str | float | bool]] = []
        for candidate in candidates:
            symbol = candidate.stock.symbol
            composite = candidate.composite_impact_score or self._scoring.score_candidate(candidate)
            rows.append(
                {
                    "symbol": symbol,
                    "analysis_exists": True,
                    "candidate_created": True,
                    "composite": composite,
                    "rejection_reason": rejection_reasons.get(symbol, ""),
                }
            )
        return rows
