"""Unified adaptive impact filter for swing and institutional paths."""

from __future__ import annotations

import structlog

from morning_trading_agent.application.services.adaptive_threshold_service import (
    AdaptiveThresholdService,
)
from morning_trading_agent.application.services.pipeline.score_safety import (
    candidate_adjusted_score,
    candidate_final_score,
)
from morning_trading_agent.application.services.candidate_filter_result import (
    CandidateFilterResult,
)
from morning_trading_agent.application.services.candidate_penalty_service import (
    CandidatePenaltyService,
)
from morning_trading_agent.application.services.candidate_rejection_logger import (
    CandidateRejectionLogger,
)
from morning_trading_agent.config.premarket_config import TradingProfileConfig
from morning_trading_agent.domain.entities.article import TradingCandidate


class AdaptiveImpactFilterService:
    """Impact-based adaptive filtering with optional penalty framework."""

    def __init__(
        self,
        *,
        profile: TradingProfileConfig,
        threshold_service: AdaptiveThresholdService | None = None,
        penalty_service: CandidatePenaltyService | None = None,
        rejection_logger: CandidateRejectionLogger | None = None,
    ) -> None:
        self._profile = profile
        self._thresholds = threshold_service or AdaptiveThresholdService()
        self._penalty = penalty_service or CandidatePenaltyService(profile=profile)
        self._rejection_log = rejection_logger or CandidateRejectionLogger()
        self._logger = structlog.get_logger(self.__class__.__name__)

    def filter_with_result(
        self,
        candidates: list[TradingCandidate],
        *,
        min_watchlist_size: int,
    ) -> CandidateFilterResult:
        selection = self._thresholds.select(
            candidates,
            min_watchlist_size=min_watchlist_size,
        )
        result = CandidateFilterResult()
        result.rejection_counts = dict(selection.rejection_counts)
        result.rejection_reasons = dict(selection.rejection_reasons)
        result.relaxation_pass_used = selection.snapshot.relaxation_pass_used
        result.adaptive_threshold_snapshot = {
            "p10": selection.snapshot.p10,
            "p25": selection.snapshot.p25,
            "p50": selection.snapshot.p50,
            "p75": selection.snapshot.p75,
            "composite_floor": selection.snapshot.composite_floor,
            "technical_floor": selection.snapshot.technical_floor,
        }

        if self._profile.use_penalty_framework:
            for candidate in selection.accepted:
                penalty_result = self._penalty.compute(candidate)
                adjusted = min(
                    100.0,
                    round(
                        candidate_final_score(candidate) * penalty_result.multiplier,
                        2,
                    ),
                )
                for pen_reason in penalty_result.reasons:
                    result.penalty_counts[pen_reason] = (
                        result.penalty_counts.get(pen_reason, 0) + 1
                    )
                result.accepted.append(
                    candidate.model_copy(
                        update={
                            "adjusted_score": adjusted,
                            "penalty_multiplier": round(penalty_result.multiplier, 4),
                            "penalty_reasons": penalty_result.reasons,
                        }
                    )
                )
            result.accepted.sort(key=candidate_adjusted_score, reverse=True)
        else:
            result.accepted = list(selection.accepted)

        for candidate in selection.rejected:
            reason = selection.rejection_reasons.get(
                candidate.stock.symbol, "below_adaptive_composite_floor"
            )
            result.rejected.append(candidate)
            self._rejection_log.log_rejection(candidate, reason, stage="adaptive_threshold")

        self._logger.info(
            "adaptive_impact_filter_complete",
            accepted=len(result.accepted),
            rejected=len(result.rejected),
            relaxation_pass_used=result.relaxation_pass_used,
        )
        return result
