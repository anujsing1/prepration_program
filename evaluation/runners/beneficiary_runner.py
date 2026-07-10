"""Beneficiary discovery evaluation runner."""

from pathlib import Path

import yaml

from evaluation.scorers.classification_metrics import EvaluationResult, precision_recall
from morning_trading_agent.agents.beneficiary.beneficiary_discovery_agent import (
    BeneficiaryDiscoveryAgent,
)
from morning_trading_agent.domain.entities.article import Article
from morning_trading_agent.infrastructure.providers.market.symbol_resolver import SymbolResolver


class BeneficiaryDiscoveryRunner:
    """Runs beneficiary discovery eval cases."""

    def __init__(self, dataset_dir: Path | None = None) -> None:
        root = Path(__file__).resolve().parents[1]
        self._dataset_dir = dataset_dir or (root / "datasets" / "beneficiary_discovery")

    async def run(self) -> EvaluationResult:
        resolver = SymbolResolver()
        resolver._load_defaults()
        resolver._loaded = True
        agent = BeneficiaryDiscoveryAgent(resolver=resolver)
        failures: list[dict[str, str]] = []
        recalls: list[float] = []

        for case_file in sorted(self._dataset_dir.glob("*.yaml")):
            case = yaml.safe_load(case_file.read_text(encoding="utf-8"))
            article = Article(
                title=case["headline"],
                content=case.get("body", case["headline"]),
                source="eval",
                published_at=__import__("datetime").datetime.now(__import__("datetime").UTC),
                url=f"eval://{case['id']}",
            )
            discovered = await agent.discover([article], [])
            actual = {m.symbol for m in discovered}
            expected = {item["symbol"] for item in case["expected"]["symbols"]}
            _, recall, _ = precision_recall(expected, actual)
            recalls.append(recall)
            if recall < 1.0:
                failures.append(
                    {
                        "case_id": case["id"],
                        "expected": ",".join(sorted(expected)),
                        "actual": ",".join(sorted(actual)),
                    }
                )

        avg_recall = sum(recalls) / len(recalls) if recalls else 0.0
        return EvaluationResult(
            module="beneficiary_discovery",
            metrics={"recall": round(avg_recall, 3)},
            failures=failures,
            passed=avg_recall >= 0.5,
        )
