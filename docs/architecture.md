# Architecture Documentation

For ranking pipeline details, see [ranking_decision_tree.md](ranking_decision_tree.md), [system_architecture.md](system_architecture.md), [debugging_guide.md](debugging_guide.md), [data_models.md](data_models.md), and [PREMARKET_PIPELINE_DIAGNOSTICS.md](PREMARKET_PIPELINE_DIAGNOSTICS.md).

## Overview

Morning Trading Agent follows Clean Architecture with Domain-Driven Design principles. Dependencies point inward: infrastructure implements interfaces defined by domain/application layers.

## ADR-001: AI Must Not Make Trading Decisions

**Decision**: LLM (Gemini) is restricted to information extraction, sentiment analysis, and report narrative generation.

**Rationale**: Trading decisions require deterministic, auditable logic. LLM outputs are non-deterministic and must not influence final rankings.

**Implementation**:
- `RankingNode` and `TechnicalAnalysisNode` have zero LLM imports
- `HybridRankingStrategy._compute_final_score()` is pure Python
- Gemini Pro only formats the watchlist report

## ADR-002: Market Data Fallback Chain

**Decision**: yfinance primary, NSE bhavcopy fallback.

**Rationale**: yfinance is reliable for NSE `.NS` tickers without API keys. Bhavcopy provides official NSE data when yfinance fails.

## ADR-003: Class-Based LangGraph Nodes

**Decision**: Each workflow step is a class implementing `GraphNode` protocol.

**Rationale**: Supports dependency injection, single responsibility, and testability. `LoggedGraphNode` decorator adds cross-cutting logging.

## Layer Dependency Rules

```
presentation → application → domain
infrastructure → application → domain
graph → application → domain
config → all layers (composition root)
```

## News Ingestion Pipeline

The news layer is orchestrated by `NewsAggregatorService` in the application layer:

1. **Fetch** — parallel provider calls via `NewsProvider` adapters (Moneycontrol, Economic Times, Google News, NSE announcements)
2. **Enrich** — `FreshnessScorer` adds `age_minutes` and `freshness_score`; `CatalystClassifier` adds `article_category` and `catalyst_score`
3. **Filter** — `FreshnessFilter` removes articles outside `NEWS_FRESHNESS_HOURS` (default 12h)
4. **Deduplicate** — `NewsDeduplication` removes duplicates by URL normalization and title similarity
5. **Log** — structured stats: fetched, removed (freshness/duplicate), analyzed, freshness distribution

Ranking incorporates freshness, catalyst priority, news priority, and full technical score breakdown via `PremarketHybridRankingStrategy`.

Quality filters remove low-liquidity, penny, duplicate-catalyst, and weak combined candidates before explainability and report generation.

## Pre-Market Pipeline

```
FetchNews → ExtractStocks → AnalyzeNews → TechnicalAnalysis → Ranking
  → FilterWatchlist → ExplainCandidates → GenerateWatchlist → PersistResults → SendTelegram
```

## Adding a New Provider

1. Create adapter class implementing the port (e.g., `NewsProvider`)
2. Register in `ProviderFactory._NEWS_ADAPTERS`
3. Add name to `NEWS_PROVIDERS` env var
4. No changes to nodes or use cases required (Open/Closed Principle)

Example — adding Zerodha market data:

```python
class ZerodhaMarketAdapter(MarketDataProvider):
    async def get_price_data(self, symbol, *, lookback_days): ...
    async def get_volume_data(self, symbol, *, lookback_days): ...
```

Register in `ProviderFactory.create_market_provider()`.

## Database Schema

Six tables store complete historical records:
- `articles` — raw news
- `sentiment_analysis` — LLM sentiment per symbol
- `technical_analysis` — deterministic indicator scores
- `watchlists` + `watchlist_entries` — ranked candidates
- `daily_reports` — generated markdown reports

## Testing Strategy

| Level | Scope | External deps |
|---|---|---|
| Unit | Domain, ranking, indicators, nodes | Mocked |
| Integration | News aggregator, cache | Mocked HTTP |
| Workflow | Full LangGraph pipeline | All mocked |

Target: 80%+ coverage enforced by pytest-cov.
