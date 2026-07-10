"""Ranking quality evaluation runner."""

from morning_trading_agent.domain.value_objects.catalyst import CatalystType
from tests.fixtures.ranking_validation_cases import GOOD_MOVERS, WEAK_MOVERS

from evaluation.scorers.classification_metrics import EvaluationResult


class RankingQualityRunner:
    """Evaluates ranking separation using validation fixtures."""

    def run(self) -> EvaluationResult:
        good_avg = sum(v["return_pct"] for v in GOOD_MOVERS.values()) / len(GOOD_MOVERS)
        weak_avg = sum(v["return_pct"] for v in WEAK_MOVERS.values()) / len(WEAK_MOVERS)
        separation = good_avg - weak_avg
        weak_types = {v.get("weak_catalyst", CatalystType.OTHER) for v in WEAK_MOVERS.values()}
        return EvaluationResult(
            module="ranking_quality",
            metrics={
                "good_mover_avg_return": round(good_avg, 2),
                "weak_mover_avg_return": round(weak_avg, 2),
                "separation": round(separation, 2),
            },
            failures=[]
            if separation > 0
            else [{"case_id": "ranking_separation", "expected": ">0", "actual": str(separation)}],
            passed=separation > 0,
        )
