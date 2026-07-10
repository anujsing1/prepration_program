#!/usr/bin/env python3
"""Benchmark local/cloud LLM providers with structured analyze_news prompts."""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

from morning_trading_agent.config.factories.llm_factory import LLMFactory
from morning_trading_agent.config.settings import Settings, get_settings
from morning_trading_agent.domain.entities.article import Article, Stock
from morning_trading_agent.infrastructure.llm.llm_telemetry import reset_llm_telemetry


def _fixture_article() -> Article:
    return Article(
        title="Reliance Industries Q4 results beat estimates",
        content="Reliance Industries reported strong quarterly earnings beating analyst estimates.",
        source="benchmark",
        published_at=datetime.now(UTC),
        url="https://example.com/reliance",
    )


def _fixture_stock() -> Stock:
    return Stock(symbol="RELIANCE", company_name="Reliance Industries")


async def _benchmark_model(
    settings: Settings,
    model: str,
    *,
    calls: int,
) -> dict:
    settings.ollama.ollama_model = model
    settings.app.llm_provider = "ollama"
    provider = LLMFactory(settings).create_llm_provider(allow_stub=False)
    reset_llm_telemetry()

    successes = 0
    for _ in range(calls):
        try:
            results = await provider.analyze_news_llm([_fixture_article()], [_fixture_stock()])
            if results:
                successes += 1
        except Exception:
            continue

    from morning_trading_agent.infrastructure.llm.llm_telemetry import get_llm_telemetry

    summary = get_llm_telemetry().summary()

    return {
        "provider": provider.provider_name,
        "model": model,
        "calls": calls,
        "successes": successes,
        "success_rate_pct": round(successes / calls * 100.0, 1) if calls else 0.0,
        "average_latency_ms": summary["average_latency_ms"],
        "p95_latency_ms": summary["p95_latency_ms"],
        "json_success_rate_pct": summary["json_success_rate_pct"],
        "failed_calls": summary["failed_calls"],
    }


def _print_table(rows: list[dict]) -> None:
    headers = [
        "Provider",
        "Model",
        "Calls",
        "Avg ms",
        "P95 ms",
        "Success %",
        "JSON %",
    ]
    print("\t".join(headers))
    for row in rows:
        print(
            "\t".join(
                [
                    str(row["provider"]),
                    str(row["model"]),
                    str(row["calls"]),
                    str(row["average_latency_ms"]),
                    str(row["p95_latency_ms"]),
                    str(row["success_rate_pct"]),
                    str(row["json_success_rate_pct"]),
                ]
            )
        )


async def _run(args: argparse.Namespace) -> list[dict]:
    settings = get_settings()
    if args.provider:
        settings.app.llm_provider = args.provider

    models = [item.strip() for item in args.models.split(",") if item.strip()]
    if not models:
        models = [settings.ollama.ollama_model]

    rows: list[dict] = []
    for model in models:
        if settings.app.llm_provider == "ollama":
            rows.append(await _benchmark_model(settings, model, calls=args.calls))
        else:
            reset_llm_telemetry()
            provider = LLMFactory(settings).create_llm_provider(allow_stub=False)
            successes = 0
            for _ in range(args.calls):
                try:
                    results = await provider.analyze_news_llm(
                        [_fixture_article()],
                        [_fixture_stock()],
                    )
                    if results:
                        successes += 1
                except Exception:
                    continue
            from morning_trading_agent.infrastructure.llm.llm_telemetry import get_llm_telemetry

            summary = get_llm_telemetry().summary()
            rows.append(
                {
                    "provider": provider.provider_name,
                    "model": getattr(settings.ollama, "ollama_model", model),
                    "calls": args.calls,
                    "successes": successes,
                    "success_rate_pct": round(successes / args.calls * 100.0, 1),
                    "average_latency_ms": summary["average_latency_ms"],
                    "p95_latency_ms": summary["p95_latency_ms"],
                    "json_success_rate_pct": summary["json_success_rate_pct"],
                    "failed_calls": summary["failed_calls"],
                }
            )
            break
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark LLM structured output latency.")
    parser.add_argument(
        "--models",
        default="",
        help="Comma-separated Ollama model tags (default: OLLAMA_MODEL from settings)",
    )
    parser.add_argument("--calls", type=int, default=10, help="Identical prompts per model")
    parser.add_argument("--provider", default="", help="Override LLM_PROVIDER for benchmark")
    parser.add_argument(
        "--output",
        default="run_report/llm_benchmark.json",
        help="Optional JSON output path",
    )
    args = parser.parse_args()

    rows = asyncio.run(_run(args))
    _print_table(rows)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"\nWrote {output_path}")


if __name__ == "__main__":
    main()
