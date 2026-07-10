"""Evaluation scoring utilities."""

from dataclasses import dataclass, field


@dataclass
class EvaluationResult:
    """Result of an evaluation module run."""

    module: str
    dataset_version: str = "v1"
    metrics: dict[str, float] = field(default_factory=dict)
    failures: list[dict[str, str]] = field(default_factory=list)
    passed: bool = True

    def to_dict(self) -> dict[str, object]:
        return {
            "module": self.module,
            "dataset_version": self.dataset_version,
            "metrics": self.metrics,
            "failures": self.failures,
            "passed": self.passed,
        }


def precision_recall(
    expected: set[str], actual: set[str]
) -> tuple[float, float, float]:
    """Compute precision, recall, and F1."""
    if not actual and not expected:
        return 1.0, 1.0, 1.0
    tp = len(expected & actual)
    precision = tp / len(actual) if actual else 0.0
    recall = tp / len(expected) if expected else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return precision, recall, f1
