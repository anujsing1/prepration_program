# Morning Trading Agent — Debugging Guide

Operational guide for diagnosing missing stocks, misclassified catalysts, rejections, score issues, and ingestion failures.

**See also:** [ranking_decision_tree.md](ranking_decision_tree.md) · [system_architecture.md](system_architecture.md) · [data_models.md](data_models.md) · [architecture.md](architecture.md)

---

## Prerequisites

1. Install dependencies from project root:

```bash
cd morning-trading-agent
uv sync
```

2. Copy and configure environment:

```bash
cp .env.example .env
# Set GEMINI_API_KEY for live runs; dry-run uses stub LLM
```

3. Enable verbose logs:

```bash
export LOG_LEVEL=DEBUG
```

---

## Primary Commands

### Run workflow (dry-run, no DB/Telegram)

```bash
cd morning-trading-agent
uv run morning-trading-agent run-morning-job --dry-run
```

### Full ranking audit in report output

```bash
uv run morning-trading-agent run-morning-job --dry-run --debug-ranking
```

### Capture logs to file

```bash
uv run morning-trading-agent run-morning-job --dry-run --debug-ranking 2>&1 | tee /tmp/mta-run.log
grep -E "candidate_rejected|extract_stocks|analyze_news|news_ingestion" /tmp/mta-run.log
```

### Live run (requires API keys)

```bash
uv run morning-trading-agent run-morning-job --date 2026-06-03
```

### Targeted unit tests

```bash
uv run pytest tests/unit/services/test_candidate_rejection.py -v --no-cov
uv run pytest tests/unit/services/test_no_direct_tradable_catalyst.py -v --no-cov
uv run pytest tests/unit/catalyst_quality/test_catalyst_escalation.py -v --no-cov
uv run pytest tests/unit/services/test_near_miss_review.py -v --no-cov
uv run pytest tests/unit/builders/test_weighted_contribution_report.py -v --no-cov
uv run pytest tests/workflow/test_trading_graph.py -v --no-cov
```

### Evaluate persisted recommendations (DB required)

```bash
# In .env: ENABLE_DATABASE=true
uv run morning-trading-agent evaluate-recommendations --date 2026-06-03
uv run morning-trading-agent show-evaluation --date 2026-06-03
```

---

## `--debug-ranking` Output Guide

When `--debug-ranking` is set, the markdown report appends a **Ranking Pipeline Debug Report** built by `RankingDebugReportBuilder`.

| Section | Contents |
|---------|----------|
| **Header stats** | Extracted, built, dropped, survived, rejected, near miss, final watchlist counts |
| **Rejection Breakdown** | Aggregated `filter_rejection_counts` |
| **Classification Summary** | Histogram of `primary_catalyst_type` from sentiments + ingestion |
| **Accepted Candidates** | Per-symbol scores + **Weighted contributions** (V2 formula lines) |
| **Rejected Candidates** | Catalyst type, magnitude/materiality/tradability, rejection reason |
| **Near Miss Candidates** | Rejected but high catalyst/tradability/materiality — manual review |
| **Pipeline Traces (collapsed)** | Up to 20 per-symbol trace summaries |

Weighted contribution line format:

```
Catalyst Score: 80 | Weight: 30% | Contribution: 24.0
```

If `weighted_*` fields are zero in breakdown but `final_score > 0`, `WeightedContributionReportBuilder` recomputes contributions from raw scores.

---

## Scenario Playbooks

### Missing stocks

**Symptom:** Expected symbol not in watchlist or not extracted.

**Check:**

1. Was the symbol extracted?

```bash
grep "extract_stocks_complete" /tmp/mta-run.log
```

Look for `symbols=[...]` and `extracted_count`.

2. Dropped at build?

```bash
grep "build_candidates_complete" /tmp/mta-run.log
```

Compare `dropped_missing_sentiment` / `dropped_missing_technical`.

3. News quality gate removed the only article mentioning the symbol?

```bash
grep "articles_removed_low_quality" /tmp/mta-run.log
```

4. Symbol resolver failed?

Check `resolved_count` vs `extracted_count` in `extract_stocks_complete`.

**State fields:** `identified_stocks`, `dropped_missing_analysis_count`, `articles`

**Tests:** `tests/workflow/test_trading_graph.py`

---

### Incorrect catalyst classification

**Symptom:** Wrong `primary_catalyst_type` or `direct_company_news` flag.

**Check:**

1. LLM vs article fallback:

```bash
grep "analyze_news_complete" /tmp/mta-run.log
```

Inspect `catalyst_types=[...]` per symbol.

2. Compare article-level vs sentiment-level type in debug report Classification Summary (`article:EARNINGS` vs `DEFENCE_PROCUREMENT`).

3. Escalation applied?

After enrich, inspect `enrich_catalyst_quality_complete` sample logs for magnitude/tradability.

4. Keyword classification on article alone:

```python
# Quick REPL check
from morning_trading_agent.application.services.news.catalyst_analysis_service import CatalystAnalysisService
from morning_trading_agent.domain.entities.article import Article
# ... build Article, service.analyze(article)
```

**Key files:** `catalyst_classification_service.py`, `catalyst_escalation_service.py`, `templates.py`

**Tests:** `tests/unit/catalyst_quality/test_catalyst_escalation.py`

---

### Rejected candidates

**Symptom:** Symbol built but not in final watchlist.

**Check:**

1. Rejection reason:

```bash
grep "candidate_rejected_catalyst" /tmp/mta-run.log
```

Fields: `symbol`, `reason`, `catalyst_type`, `direct_company_news`.

2. Aggregated counts:

```bash
grep "candidate_filter_complete" /tmp/mta-run.log
```

`rejection_counts` dict.

3. Debug report **Rejected** and **Near Miss** sections.

| Reason | Typical fix |
|--------|-------------|
| `non_tradable_catalyst` | Expected for PLANT_VISIT, ANALYST_MEETING, etc. |
| `no_direct_tradable_catalyst` | Indirect news + tradability &lt; 60; check escalation/thematic flags |
| `weak_catalyst_without_direct_news` | Raise effective catalyst or enable thematic escalation |
| `weak_catalyst_type` | Type in WEAK_CATALYST_TYPES; set `reject_weak_catalyst_types=false` only for experiments |
| `exchange_or_compliance_noise` | Exchange clarification articles |
| `penny_stock` / `low_liquidity` | Quality filter — price/volume thresholds |

**Tests:** `tests/unit/services/test_candidate_rejection.py`, `test_no_direct_tradable_catalyst.py`, `test_non_tradable_rejection.py`

---

### Ranking score calculation

**Symptom:** `final_score` does not match expected weighted sum.

**Check:**

1. Scores are set at **build_candidates**, not ranking:

```bash
grep "ranking_explanation" /tmp/mta-run.log
```

2. Inspect `score_breakdown` on candidate:

- `catalyst`, `magnitude`, `materiality`, `tradability`, `technical`, `sentiment`, `confidence`
- `weighted_*` contributions

3. Verify env weights sum to 1.0:

```
RANKING_V2_WEIGHT_CATALYST=0.30
...
```

4. Use debug report **Accepted Candidates** weighted section.

**Formula:**

```
final = 0.30×effective + 0.20×magnitude + 0.15×materiality + 0.10×tradability
      + 0.15×technical + 0.05×sentiment + 0.05×confidence
```

**Tests:** `tests/unit/ranking/test_premarket_quality_strategy.py`, `tests/unit/builders/test_weighted_contribution_report.py`

---

### Technical score calculation

**Symptom:** Unexpected `technical_score` or rejection for weak technical.

**Check:**

```bash
grep "technical_analysis_complete" /tmp/mta-run.log
```

Inspect `technical_score_distribution`.

**Inspect** `TechnicalAnalysisResult.score_breakdown`:

- `trend_strength_score`, `breakout_readiness_score`, `relative_volume_score`, `momentum_score`, etc.
- `sector_bonus`

**Note:** Two technical thresholds exist:

- `MIN_TECHNICAL_SCORE_FILTER` (50) — catalyst filter (`weak_technical_score`)
- `MIN_TECHNICAL_SCORE` (45) — watchlist quality filter (`weak_technical`)

**Tests:** `tests/unit/technical/`

---

### News ingestion failures

**Symptom:** Few or zero articles; provider errors.

**Check:**

```bash
grep -E "provider_failed|provider_fetched|news_ingestion_complete" /tmp/mta-run.log
```

| Log field | Meaning |
|-----------|---------|
| `articles_fetched` | Raw count from all providers |
| `articles_removed_freshness` | Outside session window (prev NSE close → run) or legacy `NEWS_FRESHNESS_HOURS` |
| `freshness_rejection_counts` | `prior_session_stale`, `outside_session_window`, `future_dated`, etc. |
| `session_window_start` / `session_window_end` | IST-anchored freshness window (UTC in logs) |
| `articles_removed_low_quality` | Below `MIN_ARTICLE_QUALITY_SCORE` |
| `articles_removed_duplicate` | Dedup removed |
| `articles_analyzed` | Final count after cap |
| `provider_counts` | Per-provider fetch sizes |

**`future_dated` semantics:** An article is rejected as `future_dated` only when `published_at` is more than `FUTURE_DATE_TOLERANCE_MINUTES` (default 10) ahead of filter-time `current_time`. `first_seen_at` and `fetched_at` are used for the lower bound (lifting syndicated/republished articles into the window), not for future rejection. If you see mass `future_dated` rejections with valid `published_at` timestamps, check `article_freshness_rejected` logs for `delta_seconds_vs_current` and `future_cutoff`.

**Config:** `NEWS_PROVIDERS`, `USE_SESSION_FRESHNESS`, `NSE_HOLIDAYS_PATH`, `SESSION_FETCH_BUFFER_MINUTES`, `FUTURE_DATE_TOLERANCE_MINUTES`, `NEWS_FETCH_LIMIT` (legacy: `NEWS_LOOKBACK_HOURS`, `NEWS_FRESHNESS_HOURS` when session mode off)

**Tests:** `tests/integration/providers/test_news.py`, `tests/unit/services/test_news_ingestion.py`

---

## TradingState Field Checklist

| Field | Debug question |
|-------|----------------|
| `articles` | What entered extraction? |
| `ingestion_stats` | How many removed at each gate? |
| `identified_stocks` | What symbols were extracted? |
| `sentiment_results` | Catalyst type, direct news, quality scores |
| `technical_results` | Technical score and breakdown |
| `all_candidates` | Pre-filter scores and breakdown |
| `filtered_candidates` | Survivors after filter |
| `rejected_candidates` | Full rejected candidate objects |
| `near_miss_candidates` | High-quality rejects |
| `filter_rejection_counts` | Reason → count map |
| `pipeline_traces` | Per-symbol stage audit |
| `dropped_missing_analysis_count` | Missing sentiment/technical joins |
| `ranked_candidates` | Sorted (then capped) list |
| `errors` | Workflow-level failures |

---

## Unit Test Map

| Scenario | Test file |
|----------|-----------|
| Catalyst rejection rules | `tests/unit/services/test_candidate_rejection.py` |
| GTECJAINX-style indirect reject | `tests/unit/services/test_no_direct_tradable_catalyst.py` |
| Non-tradable / exchange | `tests/unit/services/test_non_tradable_rejection.py` |
| Drone program escalation | `tests/unit/catalyst_quality/test_catalyst_escalation.py` |
| Near miss capture | `tests/unit/services/test_near_miss_review.py` |
| Weighted debug output | `tests/unit/builders/test_weighted_contribution_report.py` |
| Classification histogram | `tests/unit/builders/test_classification_summary.py` |
| News quality gate | `tests/unit/services/test_news_quality_scorer.py` |
| End-to-end dry workflow | `tests/workflow/test_trading_graph.py` |
| Rank-before-filter order | `tests/unit/ranking/test_rank_all_before_filter.py` |

---

## Database Debugging

When `ENABLE_DATABASE=true`:

| Table | Contents |
|-------|----------|
| `articles` | Ingested news |
| `analysis` / sentiment persistence | Per-run analyses |
| `watchlists` / entries | Final selections |
| `recommendation_results` | Scores, catalyst dimensions for backtest |
| `ranking_audit` | Pipeline audit rows |

Use `evaluate-recommendations` to compute EOD returns after market close.

---

## Startup Validation

On live runs, `StartupDiagnosticsService` validates Gemini key, DB, Telegram config. Failures exit with `Configuration error:` before graph runs.

The `startup_diagnostics` log includes resolved session context:

| Field | Meaning |
|-------|---------|
| `trading_session_mode` | Raw env (`AUTO` or explicit mode) |
| `detected_session` | Resolved session: `PRE_MARKET`, `INTRADAY`, `POST_MARKET` |
| `effective_session` | Alias of `detected_session` for session-aware reporting |
| `effective_strategy` | Strategy selected for detected session |
| `min_watchlist_size` | Minimum watchlist size target (`MIN_WATCHLIST_SIZE`) |
| `pro_gate_min_technical_score` / `pro_gate_min_catalyst_score` / `pro_gate_min_final_score` | Professional gate score floors from env |
| `watchlist_relaxation_enabled` | Whether gate relaxes thresholds when pool is too small |
| `rejected_by_freshness` / `rejected_by_catalyst` / `rejected_by_technical` | Rollup rejection buckets in end-of-run report |
| `watchlist_fill_rate` | `final_watchlist_size / MIN_WATCHLIST_SIZE` (capped at 1.0) |
| `relaxation_pass_used` | Progressive relaxation pass name (`freshness_minus_5`, `gate_fallback`, etc.) |
| `market_timezone` / `market_open_time` / `market_close_time` | Market clock configuration |
| `run_datetime_source` | `system_clock`, `run_datetime_override`, or `session_override` |
| `override_enabled` | `true` when `TRADING_SESSION_OVERRIDE` or `FORCE_SESSION` is set |
| `force_session` | Raw `FORCE_SESSION` env value when set |

**Freshness windows by session:**

| Session | Window |
|---------|--------|
| `PRE_MARKET` | Previous market close → run time |
| `INTRADAY` | Today market open → run time |
| `POST_MARKET` | Today market open → market close |

```bash
uv run morning-trading-agent run-morning-job  # without --dry-run
```

---

## See also

- [ranking_decision_tree.md](ranking_decision_tree.md) — rejection catalog and stage logic
- [system_architecture.md](system_architecture.md) — service and config reference
- [data_models.md](data_models.md) — field-level entity docs
