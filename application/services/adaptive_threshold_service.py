"""Distribution-based adaptive thresholds for candidate selection."""

from __future__ import annotations

from dataclasses import dataclass, field

import structlog

from morning_trading_agent.application.services.catalyst.candidate_impact_scoring_service import (
    CandidateImpactScoringService,
)
from morning_trading_agent.application.services.pipeline.score_safety import safe_float
from morning_trading_agent.config.premarket_config import AdaptiveThresholdConfig
from morning_trading_agent.domain.entities.article import TradingCandidate


@dataclass
class AdaptiveThresholdSnapshot:
    """Percentile cutoffs computed for the current candidate pool."""

    p10: float = 0.0
    p25: float = 0.0
    p50: float = 0.0
    p75: float = 0.0
    tradability_p10: float = 0.0
    tradability_p50: float = 0.0
    technical_p10: float = 0.0
    technical_p50: float = 0.0
    composite_floor: float = 0.0
    technical_floor: float = 0.0
    relaxation_pass_used: str = "none"


@dataclass
class AdaptiveSelectionResult:
    """Accepted and rejected candidates with adaptive diagnostics."""

    accepted: list[TradingCandidate] = field(default_factory=list)
    rejected: list[TradingCandidate] = field(default_factory=list)
    rejection_reasons: dict[str, str] = field(default_factory=dict)
    rejection_counts: dict[str, int] = field(default_factory=dict)
    snapshot: AdaptiveThresholdSnapshot = field(default_factory=AdaptiveThresholdSnapshot)
    impact_scores: dict[str, float] = field(default_factory=dict)


class AdaptiveThresholdService:
    """Selects candidates using current-run distribution, not fixed type gates."""

    NOISE_DIMENSION_THRESHOLD = 20.0

    def __init__(
        self,
        *,
        config: AdaptiveThresholdConfig | None = None,
        impact_scoring: CandidateImpactScoringService | None = None,
    ) -> None:
        self._config = config or AdaptiveThresholdConfig()
        self._impact = impact_scoring or CandidateImpactScoringService()
        self._logger = structlog.get_logger(self.__class__.__name__)

    def select(
        self,
        candidates: list[TradingCandidate],
        *,
        min_watchlist_size: int = 3,
    ) -> AdaptiveSelectionResult:
        if not candidates:
            return AdaptiveSelectionResult()

        impact_scores = {
            candidate.stock.symbol: self._impact.score_candidate(candidate)
            for candidate in candidates
        }
        composites = list(impact_scores.values())
        tradabilities = [
            (
                candidate.sentiment.catalyst_impact.tradability
                if candidate.sentiment.catalyst_impact
                else 50.0
            )
            for candidate in candidates
        ]
        technicals = [safe_float(candidate.technical_score) for candidate in candidates]

        snapshot = AdaptiveThresholdSnapshot(
            p10=self._percentile(composites, 10),
            p25=self._percentile(composites, 25),
            p50=self._percentile(composites, 50),
            p75=self._percentile(composites, 75),
            tradability_p10=self._percentile(tradabilities, 10),
            tradability_p50=self._percentile(tradabilities, 50),
            technical_p10=self._percentile(technicals, 10),
            technical_p50=self._percentile(technicals, 50),
        )
        snapshot.composite_floor = max(
            self._config.config_floor,
            snapshot.p50 - self._config.p50_margin,
        )
        snapshot.technical_floor = max(
            self._config.technical_floor,
            snapshot.technical_p50 - self._config.technical_margin,
        )

        result = self._apply_thresholds(
            candidates,
            impact_scores=impact_scores,
            snapshot=snapshot,
        )

        if len(result.accepted) < min_watchlist_size and candidates:
            relaxed = self._relax(snapshot)
            fallback = self._apply_thresholds(
                candidates,
                impact_scores=impact_scores,
                snapshot=relaxed,
                force_top_n=min_watchlist_size,
            )
            self._logger.info(
                "adaptive_threshold_fallback",
                accepted=len(fallback.accepted),
                min_watchlist_size=min_watchlist_size,
                composite_floor=relaxed.composite_floor,
            )
            return fallback

        return result

    def _apply_thresholds(
        self,
        candidates: list[TradingCandidate],
        *,
        impact_scores: dict[str, float],
        snapshot: AdaptiveThresholdSnapshot,
        force_top_n: int | None = None,
    ) -> AdaptiveSelectionResult:
        result = AdaptiveSelectionResult(snapshot=snapshot, impact_scores=impact_scores)
        ranked = sorted(
            candidates,
            key=lambda c: impact_scores.get(c.stock.symbol, 0.0),
            reverse=True,
        )

        for candidate in ranked:
            symbol = candidate.stock.symbol
            composite = impact_scores[symbol]
            impact = candidate.sentiment.catalyst_impact
            reason = self._reject_reason(candidate, composite, snapshot)
            if reason is None:
                updated = candidate.model_copy(
                    update={
                        "composite_impact_score": composite,
                        "effective_catalyst_score": composite,
                    }
                )
                result.accepted.append(updated)
                continue

            result.rejected.append(
                candidate.model_copy(update={"composite_impact_score": composite})
            )
            result.rejection_reasons[symbol] = reason
            result.rejection_counts[reason] = result.rejection_counts.get(reason, 0) + 1

        if force_top_n and len(result.accepted) < force_top_n:
            needed = force_top_n - len(result.accepted)
            accepted_symbols = {c.stock.symbol for c in result.accepted}
            for candidate in ranked:
                if needed <= 0:
                    break
                symbol = candidate.stock.symbol
                if symbol in accepted_symbols:
                    continue
                composite = impact_scores[symbol]
                updated = candidate.model_copy(
                    update={
                        "composite_impact_score": composite,
                        "effective_catalyst_score": composite,
                        "selection_mode": "RELAXED",
                    }
                )
                result.accepted.append(updated)
                accepted_symbols.add(symbol)
                if symbol in result.rejection_reasons:
                    old_reason = result.rejection_reasons.pop(symbol)
                    result.rejection_counts[old_reason] = max(
                        0, result.rejection_counts.get(old_reason, 0) - 1
                    )
                result.rejected = [
                    c for c in result.rejected if c.stock.symbol != symbol
                ]
                needed -= 1

        return result

    def _reject_reason(
        self,
        candidate: TradingCandidate,
        composite: float,
        snapshot: AdaptiveThresholdSnapshot,
    ) -> str | None:
        impact = candidate.sentiment.catalyst_impact
        technical = safe_float(candidate.technical_score)
        if composite >= snapshot.composite_floor:
            if technical >= snapshot.technical_floor:
                return None
            return "below_adaptive_technical_floor"

        if (
            composite < snapshot.p10
            and impact is not None
            and impact.all_below(self.NOISE_DIMENSION_THRESHOLD)
        ):
            return "below_adaptive_p10_noise"

        if composite < snapshot.composite_floor:
            if impact:
                weakest = impact.weakest_dimensions(limit=1)
                if weakest:
                    return f"below_adaptive_floor_weakest_{weakest[0][0]}"
            return "below_adaptive_composite_floor"

        if technical < snapshot.technical_floor:
            return "below_adaptive_technical_floor"
        return None

    def _relax(self, snapshot: AdaptiveThresholdSnapshot) -> AdaptiveThresholdSnapshot:
        return AdaptiveThresholdSnapshot(
            p10=snapshot.p10,
            p25=snapshot.p25,
            p50=snapshot.p50,
            p75=snapshot.p75,
            tradability_p10=snapshot.tradability_p10,
            tradability_p50=snapshot.tradability_p50,
            technical_p10=snapshot.technical_p10,
            technical_p50=snapshot.technical_p50,
            composite_floor=max(
                0.0, snapshot.composite_floor - self._config.fallback_composite_delta
            ),
            technical_floor=max(
                0.0, snapshot.technical_floor - self._config.fallback_technical_delta
            ),
            relaxation_pass_used="adaptive_fallback",
        )

    @staticmethod
    def _percentile(values: list[float], pct: int) -> float:
        if not values:
            return 0.0
        ordered = sorted(values)
        if len(ordered) == 1:
            return ordered[0]
        rank = (pct / 100.0) * (len(ordered) - 1)
        lower = int(rank)
        upper = min(lower + 1, len(ordered) - 1)
        weight = rank - lower
        return round(ordered[lower] * (1 - weight) + ordered[upper] * weight, 2)
