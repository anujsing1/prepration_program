"""Progressive candidate filtering with relaxed expansion passes."""

import structlog

from morning_trading_agent.application.services.candidate_filter_result import (
    CandidateFilterResult,
)
from morning_trading_agent.application.services.candidate_filter_service import (
    CandidateFilterService,
)
from morning_trading_agent.domain.entities.article import TradingCandidate
from morning_trading_agent.config.premarket_config import (
    AdaptiveWatchlistConfig,
    FilterRelaxationOverlay,
    ProgressiveRelaxationConfig,
)

NON_RELAXABLE_REJECTION_REASONS: frozenset[str] = frozenset(
    {
        "exchange_or_compliance_noise",
        "non_tradable_catalyst",
    }
)


class AdaptiveCandidateFilterService:
    """Strict pass first; progressive relaxation if below minimum watchlist size."""

    def __init__(
        self,
        *,
        strict_filter: CandidateFilterService,
        adaptive_config: AdaptiveWatchlistConfig | None = None,
        progressive_config: ProgressiveRelaxationConfig | None = None,
        base_min_freshness: float = 70.0,
    ) -> None:
        self._strict = strict_filter
        self._adaptive = adaptive_config or AdaptiveWatchlistConfig()
        self._progressive = progressive_config or ProgressiveRelaxationConfig()
        self._base_min_freshness = base_min_freshness
        self._logger = structlog.get_logger(self.__class__.__name__)

    def filter_with_result(
        self,
        candidates: list[TradingCandidate],
        *,
        min_watchlist_size: int,
    ) -> CandidateFilterResult:
        """Run strict filter; optionally relax and re-admit rejects."""
        strict_overlay = FilterRelaxationOverlay(
            pass_name="strict",
            min_freshness_override=self._base_min_freshness,
        )
        result = self._strict.filter_with_result(candidates, overlay=strict_overlay)

        if (
            not self._adaptive.enabled
            or len(result.accepted) >= min_watchlist_size
            or not result.rejected
        ):
            return result

        self._logger.info(
            "watchlist_expansion_triggered",
            accepted=len(result.accepted),
            minimum=min_watchlist_size,
            rejected_pool=len(result.rejected),
        )

        combined = CandidateFilterResult()
        combined.accepted = list(result.accepted)
        combined.rejected = list(result.rejected)
        combined.rejection_counts = dict(result.rejection_counts)
        combined.rejection_reasons = dict(result.rejection_reasons)

        relaxable = [
            c
            for c in result.rejected
            if result.rejection_reasons.get(c.stock.symbol) not in NON_RELAXABLE_REJECTION_REASONS
        ]
        hard_rejected = [
            c
            for c in result.rejected
            if result.rejection_reasons.get(c.stock.symbol) in NON_RELAXABLE_REJECTION_REASONS
        ]

        remaining = relaxable
        last_pass = "none"
        gate_freshness_override: float | None = None

        for overlay in self._progressive_passes():
            if len(combined.accepted) >= min_watchlist_size or not remaining:
                break

            pass_result = self._strict.filter_with_result(remaining, overlay=overlay)
            if not pass_result.accepted:
                continue

            last_pass = overlay.pass_name
            if overlay.min_freshness_override is not None:
                gate_freshness_override = overlay.min_freshness_override

            for candidate in pass_result.accepted:
                combined.accepted.append(
                    candidate.model_copy(update={"selection_mode": "RELAXED"})
                )
            remaining = pass_result.rejected
            for reason, count in pass_result.rejection_counts.items():
                combined.rejection_counts[reason] = (
                    combined.rejection_counts.get(reason, 0) + count
                )
            combined.rejection_reasons.update(pass_result.rejection_reasons)

            self._logger.info(
                "watchlist_relaxation_pass",
                pass_name=overlay.pass_name,
                accepted_added=len(pass_result.accepted),
                total_accepted=len(combined.accepted),
                remaining_rejected=len(remaining),
            )

        combined.rejected = hard_rejected + remaining
        combined.relaxation_pass_used = last_pass if last_pass != "none" else "none"
        combined.gate_min_freshness_override = gate_freshness_override

        relaxed_added = sum(1 for c in combined.accepted if c.selection_mode == "RELAXED")
        self._logger.info(
            "watchlist_expansion_complete",
            strict_accepted=len(result.accepted),
            relaxed_added=relaxed_added,
            total_accepted=len(combined.accepted),
            still_rejected=len(combined.rejected),
            relaxation_pass_used=combined.relaxation_pass_used,
        )
        return combined

    def _progressive_passes(self) -> list[FilterRelaxationOverlay]:
        base = self._base_min_freshness
        cfg = self._progressive
        return [
            FilterRelaxationOverlay(
                pass_name="freshness_minus_5",
                min_freshness_override=max(0.0, base - cfg.freshness_pass1_delta),
            ),
            FilterRelaxationOverlay(
                pass_name="freshness_minus_15",
                min_freshness_override=max(0.0, base - cfg.freshness_pass2_total_delta),
            ),
            FilterRelaxationOverlay(
                pass_name="allow_secondary_catalysts",
                allow_secondary_catalysts=True,
            ),
            FilterRelaxationOverlay(
                pass_name="technical_rescue_60",
                technical_rescue_min=cfg.technical_rescue_min,
            ),
        ]
