# Pipeline Debugging Guide

This guide explains how to diagnose pipeline bottlenecks, empty watchlists, and per-symbol lifecycle issues using the audit framework emitted on every `make run` / `make run-dry` execution.

## Quick Start

```bash
# Full live run (writes .artifacts/ and prints funnel at end)
make run

# Offline dry-run with audit artifacts
make run-dry

# Trace one symbol from latest artifacts
make trace SYMBOL=RELIANCE

# Re-run pipeline then trace
make trace SYMBOL=RELIANCE FRESH=1 DRY=1
```

At workflow completion the console prints:

```
=== PIPELINE FUNNEL ===
=== TOP REJECTION REASONS ===
=== TOP CATALYST TYPES ===
=== TOP DROP-OFF STAGES ===
=== EMPTY WATCHLIST ANALYSIS ===
```

## Audit Artifacts

All files are written to `.artifacts/` on every run.

| File | Contents |
|------|----------|
| `run_audit.json` | Funnel metrics, largest drop-off stage, top rejection/catalyst summaries |
| `run_audit.md` | Human-readable funnel table |
| `articles_audit.json` | Per-article ingestion: source, title, catalyst type, accept/reject |
| `extraction_audit.json` | Per-article symbol extraction method and failures |
| `classification_audit.json` | Per-stock catalyst classification path and OTHER reasons |
| `tradability_audit.json` | Per-stock tradability score breakdown |
| `candidate_audit.json` | Per-candidate scores, tier, rejection reasons |
| `technical_audit.json` | Per-symbol RSI, momentum, RVOL, EMA trend, rule pass/fail |
| `ranking_audit.json` | Per-candidate ranking position, component scores, penalties |
| `watchlist_selection_audit.json` | Why each symbol was selected or not selected |
| `root_cause_analysis.md` | Generated only when final watchlist size is 0 |

## Funnel Stages

The end-to-end funnel tracks entity counts through these stages:

1. **articles_fetched** — Raw articles from all news providers
2. **articles_after_dedup** — After fetch-time quality, freshness, and dedup
3. **articles_rejected_by_freshness** — Stale/outside-session articles
4. **articles_rejected_by_quality** — Low quality at fetch or low ingress score
5. **articles_rejected_by_spam** — Spam/noise filter (short content, macro-only, etc.)
6. **articles_accepted** — Articles entering stock extraction
7. **symbol_extraction** — Accepted articles → resolved NSE symbols
8. **catalyst_classification** — Extracted stocks → classified sentiments
9. **tradability_evaluation** — Classified stocks → tradable catalysts
10. **candidate_creation** — Join sentiment + technical into candidates
11. **technical_analysis** — Technical data availability (diagnostic pass-through)
12. **ranking** — Scored and sorted candidates
13. **watchlist_selection** — Filter survivors → final watchlist

Each stage records:

- `input_count`
- `output_count`
- `drop_count`
- `drop_percentage`

The largest drop-off stage and any stage with **>50% entity loss** are highlighted in `run_audit.json` and the console summary.

## Structured Log Events

Search logs for these events when debugging live runs:

| Event | Stage | When |
|-------|-------|------|
| `article_ingested` | Fetch | Article passes fetch-time enrichment |
| `article_accepted` | Ingress | Article passes spam/ingress gate |
| `article_rejected` | Ingress | Article rejected with reason |
| `symbol_extraction_success` | Extraction | Primary symbol resolved for article |
| `symbol_extraction_failure` | Extraction | No resolvable NSE symbol |
| `classifier_input` | Classification | LLM/raw input before enrichment |
| `classifier_output` | Classification | Final catalyst type assigned |
| `taxonomy_match` | Classification | Matched existing taxonomy entry |
| `taxonomy_fallback` | Classification | Proposed new taxonomy code |
| `other_assignment_reason` | Classification | Why `OTHER` was assigned |
| `pipeline_event` | All candidate stages | Per-symbol stage pass/fail |
| `watchlist_select_dropped` | Selection | Symbol dropped at tier/cap selection |
| `pipeline_run_audit_written` | Completion | All artifacts saved |

## Diagnosing Empty Watchlists

1. Open `.artifacts/run_audit.md` and find the **largest drop-off stage**.
2. Read `.artifacts/root_cause_analysis.md` (auto-generated when watchlist size = 0).
3. Check **top rejection reasons** in console output or `run_audit.json`.
4. Drill into stage-specific files:
   - Early funnel empty → `articles_audit.json`, `extraction_audit.json`
   - Classification collapse → `classification_audit.json` (look for `OTHER` and `other_assignment_reason`)
   - Late-stage filtering → `candidate_audit.json`, `watchlist_selection_audit.json`

Common patterns:

| Symptom | Likely stage | Check |
|---------|--------------|-------|
| Few articles reach extraction | Ingress/spam | `articles_rejected_by_spam`, `content_too_short` counts |
| Articles but no stocks | Symbol extraction | `extraction_audit.json` failure_reason |
| Stocks but all OTHER | Classification | `classification_audit.json`, `other_assignment_reason` logs |
| Candidates but empty watchlist | Selection/filter | `watchlist_selection_audit.json`, `select_drop_counts` |

## Tracing a Single Stock

```bash
make trace SYMBOL=RELIANCE
```

This prints the full lifecycle:

```
Article → Extraction → Classification → Tradability → Technical → Ranking → Selection
```

By default, trace reads the most recent `.artifacts/` from the last pipeline run. Use `FRESH=1` to re-run first.

## Identifying Bottlenecks

1. Run `make run-dry` or `make run`.
2. Review console **TOP DROP-OFF STAGES** section.
3. Any stage with **>50% drop** is flagged under **STAGES WITH >50% ENTITY LOSS**.
4. Cross-reference the stage-specific JSON audit file for per-entity reasons.
5. Use `make trace SYMBOL=XYZ` to inspect one entity end-to-end.

## Design Notes

- The audit framework is **generic** — no symbol-specific rules, whitelists, or hardcoded catalyst handling.
- Audit collection is **read-only** — it does not change ranking thresholds, catalyst scores, technical filters, or watchlist selection logic.
- Technical rule pass/fail in `technical_audit.json` is **diagnostic only** (for observability), not used in filtering decisions.

## Related Commands

| Command | Purpose |
|---------|---------|
| `make run-debug` | Dry-run + ranking debug report in markdown output |
| `make debug-pipeline` | Run individual stages with stage-level diagnostics |
| `make run-news` … `make run-reporting` | Modular workflows with per-stage JSON artifacts |

See also: [MAKEFILE_REFERENCE.md](./MAKEFILE_REFERENCE.md), [USAGE_GUIDE.md](./USAGE_GUIDE.md).
