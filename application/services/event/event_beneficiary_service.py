"""Event-level beneficiary caps replacing global duplicate_catalyst."""

import structlog

from morning_trading_agent.config.premarket_config import WatchlistQualityConfig
from morning_trading_agent.domain.entities.article import TradingCandidate
from morning_trading_agent.domain.entities.event import EventRecord


class EventBeneficiaryService:
    """Applies per-event beneficiary limits instead of global catalyst-type dedup."""

    def __init__(self, *, config: WatchlistQualityConfig | None = None) -> None:
        self._config = config or WatchlistQualityConfig()
        self._logger = structlog.get_logger(self.__class__.__name__)

    def apply_event_caps(
        self,
        candidates: list[TradingCandidate],
        events: list[EventRecord],
    ) -> tuple[list[TradingCandidate], list[TradingCandidate]]:
        """Keep top beneficiaries per event cluster by weighted final score."""
        if not events:
            return candidates, []

        event_by_symbol: dict[str, str] = {}
        for event in events:
            for beneficiary in event.beneficiaries:
                event_by_symbol[beneficiary.symbol] = event.event_id

        grouped: dict[str, list[TradingCandidate]] = {}
        no_event: list[TradingCandidate] = []
        for candidate in candidates:
            eid = candidate.event_id or event_by_symbol.get(candidate.stock.symbol, "")
            if not eid:
                no_event.append(candidate)
                continue
            grouped.setdefault(eid, []).append(candidate)

        accepted: list[TradingCandidate] = list(no_event)
        rejected: list[TradingCandidate] = []
        max_per = self._config.max_symbols_per_event
        min_weight = self._config.min_event_beneficiary_weight

        for event_id, group in grouped.items():
            group.sort(
                key=lambda c: (
                    -(c.beneficiary_weight or 0),
                    -c.final_score,
                )
            )
            kept = 0
            for rank_in_group, candidate in enumerate(group, start=1):
                weight = candidate.beneficiary_weight or 1.0
                symbol = candidate.stock.symbol
                if weight < min_weight:
                    rejected.append(candidate)
                    self._logger.info(
                        "event_cap_candidate_rejected",
                        symbol=symbol,
                        event_id=event_id,
                        reason="event_cap_low_weight",
                        rank_in_event_group=rank_in_group,
                        beneficiary_weight=weight,
                        min_event_beneficiary_weight=min_weight,
                        max_symbols_per_event=max_per,
                        final_score=candidate.final_score,
                        removal_mandatory=False,
                        configurable_threshold="min_event_beneficiary_weight",
                    )
                    continue
                if kept < max_per:
                    accepted.append(candidate)
                    kept += 1
                    self._logger.info(
                        "event_cap_candidate_kept",
                        symbol=symbol,
                        event_id=event_id,
                        rank_in_event_group=rank_in_group,
                        beneficiary_weight=weight,
                        max_symbols_per_event=max_per,
                        kept_count=kept,
                        final_score=candidate.final_score,
                    )
                else:
                    rejected.append(candidate)
                    self._logger.info(
                        "event_cap_candidate_rejected",
                        symbol=symbol,
                        event_id=event_id,
                        reason="event_cap_overflow",
                        rank_in_event_group=rank_in_group,
                        beneficiary_weight=weight,
                        max_symbols_per_event=max_per,
                        final_score=candidate.final_score,
                        removal_mandatory=True,
                        configurable_threshold="max_symbols_per_event",
                        code_path="EventBeneficiaryService.apply_event_caps",
                    )

        for candidate in no_event:
            self._logger.info(
                "event_cap_candidate_bypassed",
                symbol=candidate.stock.symbol,
                reason="no_event_id_mapping",
                final_score=candidate.final_score,
                code_path="EventBeneficiaryService.apply_event_caps",
            )

        self._logger.info(
            "event_beneficiary_caps_applied",
            input=len(candidates),
            accepted=len(accepted),
            rejected=len(rejected),
        )
        return accepted, rejected
