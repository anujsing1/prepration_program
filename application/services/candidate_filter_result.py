"""Structured result from candidate filtering."""

from dataclasses import dataclass, field

from morning_trading_agent.domain.entities.article import TradingCandidate


@dataclass
class CandidateFilterResult:
    """Accepted/rejected candidates with per-reason counts."""

    accepted: list[TradingCandidate] = field(default_factory=list)
    rejected: list[TradingCandidate] = field(default_factory=list)
    rejection_counts: dict[str, int] = field(default_factory=dict)
    rejection_reasons: dict[str, str] = field(default_factory=dict)
    penalty_counts: dict[str, int] = field(default_factory=dict)
    relaxation_pass_used: str = "none"
    gate_min_freshness_override: float | None = None
    adaptive_threshold_snapshot: dict[str, float] = field(default_factory=dict)

    def record_rejection(self, candidate: TradingCandidate, reason: str) -> None:
        self.rejection_counts[reason] = self.rejection_counts.get(reason, 0) + 1
        self.rejection_reasons[candidate.stock.symbol] = reason
