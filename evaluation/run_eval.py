"""Evaluation CLI entrypoint."""

import asyncio
import json
import sys
from pathlib import Path

import click

from evaluation.runners.beneficiary_runner import BeneficiaryDiscoveryRunner
from evaluation.runners.ranking_runner import RankingQualityRunner


@click.command("evaluate")
@click.option(
    "--module",
    type=click.Choice(["beneficiary_discovery", "ranking_quality", "all"]),
    default="all",
)
def evaluate_cli(module: str) -> None:
    """Run evaluation modules against curated datasets."""
    results = []

    async def _run() -> None:
        if module in {"beneficiary_discovery", "all"}:
            results.append(await BeneficiaryDiscoveryRunner().run())
        if module in {"ranking_quality", "all"}:
            results.append(RankingQualityRunner().run())

    asyncio.run(_run())
    for result in results:
        click.echo(json.dumps(result.to_dict(), indent=2))
    if any(not r.passed for r in results):
        sys.exit(1)


if __name__ == "__main__":
    evaluate_cli()
