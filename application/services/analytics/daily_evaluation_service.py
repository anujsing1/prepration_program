"""Daily performance analytics over evaluated recommendations."""

from dataclasses import dataclass, field
from datetime import date
from statistics import mean, median

from morning_trading_agent.domain.entities.recommendation_result import RecommendationResult
from morning_trading_agent.domain.repositories.recommendation_result_repository import (
    RecommendationResultRepository,
)
from morning_trading_agent.domain.value_objects.catalyst import CatalystType


@dataclass
class DailyEvaluationReport:
    """Aggregated performance metrics for a trade date."""

    trade_date: date
    total_count: int = 0
    evaluated_count: int = 0
    win_rate: float = 0.0
    average_return: float = 0.0
    median_return: float = 0.0
    best_catalyst_type: str = ""
    worst_catalyst_type: str = ""
    best_catalyst_avg_return: float = 0.0
    worst_catalyst_avg_return: float = 0.0
    top_5_avg_return: float = 0.0
    top_10_avg_return: float = 0.0
    bottom_5_avg_return: float = 0.0
    by_catalyst: dict[str, float] = field(default_factory=dict)

    def to_markdown(self) -> str:
        lines = [
            f"# Daily Evaluation — {self.trade_date.isoformat()}",
            "",
            f"- **Recommendations:** {self.total_count}",
            f"- **Evaluated:** {self.evaluated_count}",
            f"- **Win rate:** {self.win_rate:.1f}%",
            f"- **Average return:** {self.average_return:.2f}%",
            f"- **Median return:** {self.median_return:.2f}%",
            f"- **Top 5 avg return:** {self.top_5_avg_return:.2f}%",
            f"- **Top 10 avg return:** {self.top_10_avg_return:.2f}%",
            f"- **Bottom 5 avg return:** {self.bottom_5_avg_return:.2f}%",
            f"- **Best catalyst:** {self.best_catalyst_type} ({self.best_catalyst_avg_return:.2f}%)",
            f"- **Worst catalyst:** {self.worst_catalyst_type} ({self.worst_catalyst_avg_return:.2f}%)",
            "",
        ]
        if self.by_catalyst:
            lines.append("## Returns by catalyst type")
            lines.append("")
            for catalyst, avg in sorted(self.by_catalyst.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"- **{catalyst}:** {avg:.2f}%")
        return "\n".join(lines)


class DailyEvaluationService:
    """Computes performance metrics from recommendation_results."""

    def __init__(self, repository: RecommendationResultRepository) -> None:
        self._repository = repository

    async def evaluate(self, trade_date: date) -> DailyEvaluationReport:
        """Build analytics report for a trade date."""
        records = await self._repository.find_by_trade_date(trade_date)
        evaluated = [r for r in records if r.close_return_pct is not None]
        returns = [r.close_return_pct for r in evaluated if r.close_return_pct is not None]

        report = DailyEvaluationReport(
            trade_date=trade_date,
            total_count=len(records),
            evaluated_count=len(evaluated),
        )
        if not returns:
            return report

        report.average_return = mean(returns)
        report.median_return = median(returns)
        wins = sum(1 for value in returns if value > 0)
        report.win_rate = (wins / len(returns)) * 100.0

        sorted_by_rank = sorted(evaluated, key=lambda r: r.rank)
        top_5 = [r.close_return_pct for r in sorted_by_rank[:5] if r.close_return_pct is not None]
        top_10 = [r.close_return_pct for r in sorted_by_rank[:10] if r.close_return_pct is not None]
        bottom_5 = [
            r.close_return_pct
            for r in sorted(evaluated, key=lambda r: r.rank, reverse=True)[:5]
            if r.close_return_pct is not None
        ]
        if top_5:
            report.top_5_avg_return = mean(top_5)
        if top_10:
            report.top_10_avg_return = mean(top_10)
        if bottom_5:
            report.bottom_5_avg_return = mean(bottom_5)

        catalyst_returns: dict[CatalystType, list[float]] = {}
        for record in evaluated:
            if record.close_return_pct is None:
                continue
            catalyst_returns.setdefault(record.catalyst_type, []).append(record.close_return_pct)

        for catalyst, values in catalyst_returns.items():
            report.by_catalyst[catalyst.value] = mean(values)

        if report.by_catalyst:
            best = max(report.by_catalyst.items(), key=lambda x: x[1])
            worst = min(report.by_catalyst.items(), key=lambda x: x[1])
            report.best_catalyst_type = best[0]
            report.best_catalyst_avg_return = best[1]
            report.worst_catalyst_type = worst[0]
            report.worst_catalyst_avg_return = worst[1]

        return report
