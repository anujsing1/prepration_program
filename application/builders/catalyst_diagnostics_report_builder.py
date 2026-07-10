"""Catalyst acceptance/rejection diagnostics for pipeline reports."""

from collections import Counter

from morning_trading_agent.domain.value_objects.catalyst_tradability import (
    TRADABILITY_BUCKETS,
    AcceptedCatalystDiagnostic,
    RejectedCandidateDiagnostic,
)
from morning_trading_agent.graph.state import TradingState


class CatalystDiagnosticsReportBuilder:
    """Builds catalyst-focused diagnostic markdown sections."""

    def build_sections(self, state: TradingState) -> str:
        accepted = list(state.get("accepted_catalyst_diagnostics", []))
        rejected = self._collect_rejected(state)
        sections: list[str] = []

        if accepted:
            sections.extend(self._accepted_section(accepted))
        if rejected:
            sections.extend(self._rejected_section(rejected))

        distribution = self._catalyst_distribution(accepted, rejected)
        if distribution:
            sections.extend(distribution)

        rejection_reasons = self._rejection_reasons(rejected, state)
        if rejection_reasons:
            sections.extend(rejection_reasons)

        tradability_distribution = self._tradability_distribution(accepted, rejected)
        if tradability_distribution:
            sections.extend(tradability_distribution)

        return "\n".join(sections)

    @staticmethod
    def _collect_rejected(state: TradingState) -> list[RejectedCandidateDiagnostic]:
        details = list(state.get("tradability_rejections", []))
        seen = {detail.symbol for detail in details}
        reason_map = {
            trace.symbol: trace.rejection_reason
            for trace in state.get("pipeline_traces", [])
            if trace.rejected and trace.rejection_reason
        }
        for candidate in state.get("rejected_candidates", []):
            symbol = candidate.stock.symbol
            if symbol in seen:
                continue
            profile = candidate.sentiment.catalyst_tradability
            if profile is None:
                continue
            reason = reason_map.get(symbol) or profile.rejection_reason or "filtered"
            details.append(
                RejectedCandidateDiagnostic(
                    symbol=symbol,
                    catalyst_type=candidate.sentiment.primary_catalyst_type.value,
                    tradable=profile.tradable,
                    tradability_score=profile.tradability_score,
                    rejection_reason=reason,
                )
            )
            seen.add(symbol)
        return details

    @staticmethod
    def _accepted_section(accepted: list[AcceptedCatalystDiagnostic]) -> list[str]:
        lines = ["## Accepted Catalysts", ""]
        for item in accepted:
            lines.append(item.format_line())
        lines.append("")
        return lines

    @staticmethod
    def _rejected_section(rejected: list[RejectedCandidateDiagnostic]) -> list[str]:
        lines = ["## Rejected Catalysts", ""]
        for item in rejected:
            lines.append(item.format_line())
        lines.append("")
        return lines

    @staticmethod
    def _catalyst_distribution(
        accepted: list[AcceptedCatalystDiagnostic],
        rejected: list[RejectedCandidateDiagnostic],
    ) -> list[str]:
        accepted_counts = Counter(item.catalyst_type for item in accepted)
        rejected_counts = Counter(item.catalyst_type for item in rejected)
        if not accepted_counts and not rejected_counts:
            return []
        lines = ["## Catalyst Distribution", ""]
        all_types = sorted(set(accepted_counts) | set(rejected_counts))
        for catalyst_type in all_types:
            lines.append(
                f"- {catalyst_type}: accepted={accepted_counts.get(catalyst_type, 0)}, "
                f"rejected={rejected_counts.get(catalyst_type, 0)}"
            )
        lines.append("")
        return lines

    @staticmethod
    def _rejection_reasons(
        rejected: list[RejectedCandidateDiagnostic],
        state: TradingState,
    ) -> list[str]:
        counts = Counter(item.rejection_reason for item in rejected)
        for reason, count in state.get("filter_rejection_counts", {}).items():
            counts[reason] += count
        if not counts:
            return []
        lines = ["## Rejection Reasons", ""]
        for reason, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"- {reason}: {count}")
        lines.append("")
        return lines

    @staticmethod
    def _tradability_distribution(
        accepted: list[AcceptedCatalystDiagnostic],
        rejected: list[RejectedCandidateDiagnostic],
    ) -> list[str]:
        scores = [item.tradability_score for item in accepted]
        scores.extend(item.tradability_score for item in rejected)
        if not scores:
            return []
        bucket_counts = {label: 0 for label, _, _ in TRADABILITY_BUCKETS}
        for score in scores:
            for label, low, high in TRADABILITY_BUCKETS:
                if low <= score <= high:
                    bucket_counts[label] += 1
                    break
        lines = ["## Tradability Distribution", ""]
        for label, _, _ in TRADABILITY_BUCKETS:
            lines.append(f"- {label}: {bucket_counts[label]}")
        lines.append("")
        return lines
