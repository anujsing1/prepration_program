# Makefile Command Reference

Quick reference for all `make` targets in the Morning Trading Agent project.

**New to the project?** Start with the scenario-based guide: [USAGE_GUIDE.md](./USAGE_GUIDE.md).

**Location:** run all commands from the project root:

```bash
cd morning-trading-agent
```

**Built-in help:**

```bash
make help
```

---

## Makefile variables

These can be passed on the command line to override defaults.

| Variable | Default | Used by |
|----------|---------|---------|
| `DATE` | Today's date (`YYYY-MM-DD`) | `eval-recommendations`, `show-evaluation`, `THREAD_ID`, research desk default report paths |
| `THREAD_ID` | `{DATE}_morning` | `run-resume` |
| `BACKTEST_FROM` | `2026-06-01` | `backtest`, `backtest-dry` |
| `BACKTEST_TO` | `2026-06-05` | `backtest`, `backtest-dry` |
| `SESSION` | — | `make run` (optional: `premarket`, `intraday`, `postmarket`) |
| `AT` | — | `make run` (ISO datetime override, e.g. `2026-07-03T08:30:00`) |
| `DRY` | — | `run-premarket`, `run-intraday`, `run-postmarket`, `research-desk-*` (set `DRY=1` for dry-run) |
| `OUT` | — | `research-desk-postmarket`, `research-desk-premarket` (custom report path) |
| `NO_STRICT` | — | `research-desk-*` (set `NO_STRICT=1` to continue when critical agents lack live data) |
| `SYMBOL` | — | `make trace` (required) |
| `FRESH` | — | `make trace` (set `FRESH=1` to bypass LLM cache) |
| `ID` | — | `approve-catalyst`, `reject-catalyst` (required) |

**Examples:**

```bash
make eval-recommendations DATE=2026-06-05
make show-evaluation DATE=2026-06-05
make run-resume THREAD_ID=2026-06-05_morning
make backtest BACKTEST_FROM=2026-06-01 BACKTEST_TO=2026-06-10
make run SESSION=premarket
make research-desk-premarket OUT=run_report/my_premarket.md
make research-desk-postmarket NO_STRICT=1 DRY=1
```

---

## 1. Setup and quality

| Make command | Underlying command | Description |
|--------------|-------------------|-------------|
| `make setup` | `uv venv` + `pip install -e ".[dev]"` | Create `.venv` and install dependencies |
| `make install` | Same as `setup` | Alias for first-time setup |
| `make lint` | `ruff check src tests` | Lint source and tests |
| `make format` | `black` + `ruff --fix` | Format and auto-fix code |
| `make typecheck` | `mypy src` | Static type checking |
| `make test` | `pytest tests/ -v` | Full test suite (80% coverage gate) |
| `make test-cov` | `pytest` + coverage report | Tests with missing-line report |
| `make migrate` | `alembic upgrade head` | Apply database migrations |

**First-time onboarding:**

```bash
make setup
make run-dry
```

---

## 2. Full pipeline

Runs the complete morning watchlist job via `app.py run-morning-job`.

| Make command | CLI equivalent | Mode | Requirements |
|--------------|----------------|------|--------------|
| `make run` | `python app.py run-morning-job` | **Live** | `GEMINI_API_KEY` in `.env` |
| `make run-dry` | `python app.py run-morning-job --dry-run` | **Dry-run** | None (stub LLM/market) |
| `make run-debug` | `... --dry-run --debug-ranking` | **Dry-run + audit** | None |
| `make run-resume` | `... --resume --thread-id $(THREAD_ID)` | **Checkpoint resume** | `ENABLE_CHECKPOINTING=true`, PostgreSQL, `.[checkpoint]` installed |

### Trading session watchlist jobs

Force a specific market session on the watchlist pipeline (`run-morning-job`).

| Make command | CLI equivalent | Description |
|--------------|----------------|-------------|
| `make run-premarket` | `run-morning-job --session premarket` | Pre-market watchlist (strategy from `PREMARKET_STRATEGY`) |
| `make run-intraday` | `run-morning-job --session intraday` | Intraday watchlist |
| `make run-postmarket` | `run-morning-job --session postmarket` | Post-market review watchlist |

Append `DRY=1` for dry-run on any session target:

```bash
make run-premarket DRY=1
make run-postmarket
```

Optional overrides on `make run`:

```bash
make run SESSION=premarket
make run SESSION=postmarket AT="2026-07-03T16:00:00"
```

**Notes:**

- Live runs use real Gemini, news providers, and market data.
- Dry-run skips DB persistence and Telegram unless explicitly enabled.
- Resume requires checkpointing to be enabled and a valid `THREAD_ID`.

---

## 2b. Institutional research desk

Separate multi-agent intelligence layer (`app.py run-research-desk`). Builds or consumes `market_memory/` for RAG-backed pre/post-market analysis. See [RESEARCH_DESK_AUDIT.md](./RESEARCH_DESK_AUDIT.md).

| Make command | CLI equivalent | When to use |
|--------------|----------------|-------------|
| `make research-desk-postmarket` | `run-research-desk --mode postmarket --session postmarket` | After market close — seeds `market_memory/YYYY/MM/YYYY-MM-DD/` |
| `make research-desk-premarket` | `run-research-desk --mode premarket --session premarket` | Before open — loads prior memory, validates yesterday's thesis |

**Default report paths** (created under `run_report/`):

| Target | Default output |
|--------|----------------|
| `research-desk-postmarket` | `run_report/research_desk_postmarket_$(DATE).md` |
| `research-desk-premarket` | `run_report/research_desk_premarket_$(DATE).md` |

**Make variables:**

| Variable | Effect |
|----------|--------|
| `OUT=path/to/report.md` | Custom executive report path |
| `DATE=2026-07-03` | Session date (`--date`) and default filename |
| `DRY=1` | Keyword embeddings only (no Ollama/Gemini) |
| `NO_STRICT=1` | Continue when critical agents lack live data (not recommended for production) |

**Examples:**

```bash
# Post-market institutional deck (live, strict)
make research-desk-postmarket

# Pre-market deck with custom output
make research-desk-premarket OUT=run_report/research_desk_premarket_live.md

# Offline smoke test
make research-desk-premarket DRY=1 NO_STRICT=1
```

**Requirements (live):**

| Variable | Typical value |
|----------|---------------|
| `ENABLE_RESEARCH_DESK` | `true` |
| `LLM_PROVIDER` | `ollama` or `gemini` |
| `OLLAMA_BASE_URL` | `http://localhost:11434/v1` (if Ollama) |
| `OLLAMA_MODEL` | `qwen2.5:7b` |
| `RAG_EMBEDDING_MODEL` | `nomic-embed-text` |
| `MARKET_MEMORY_PATH` | `market_memory` |
| `MARKET_MEMORY_TOP_K` | `5` |

**Artifacts:**

| Path | Contents |
|------|----------|
| `run_report/research_desk_*.md` | Executive research report |
| `market_memory/YYYY/MM/YYYY-MM-DD/memory.json` | Persisted session for RAG |
| `.artifacts/research_desk/*_agent_health.json` | Per-agent health records |

**Direct CLI (equivalent):**

```bash
python app.py run-research-desk --mode premarket --session premarket \
  --output run_report/research_desk_premarket_live.md
```

---

## 3. Modular workflows (dry-run)

Runs individual workflow modules. Each target uses `--dry-run` and writes JSON artifacts under `.artifacts/`.

| Make command | CLI equivalent | Input artifacts | Output directory |
|--------------|----------------|-----------------|------------------|
| `make run-news` | `run-news-workflow --dry-run --output .artifacts/news` | — | `.artifacts/news/` |
| `make run-research` | `run-research-workflow --dry-run --input .artifacts/news --output .artifacts/research` | `.artifacts/news/` | `.artifacts/research/` |
| `make run-technical` | `run-technical-workflow --dry-run --input .artifacts/research --output .artifacts/technical` | `.artifacts/research/` | `.artifacts/technical/` |
| `make run-ranking` | `run-ranking-workflow --dry-run --input .artifacts/technical --output .artifacts/ranking` | `.artifacts/technical/` | `.artifacts/ranking/` |
| `make run-watchlist` | `run-watchlist-workflow --dry-run --input .artifacts/ranking --output .artifacts/watchlist` | `.artifacts/ranking/` | `.artifacts/watchlist/` |
| `make run-reporting` | `run-reporting-workflow --dry-run --input .artifacts/watchlist --output .artifacts/reporting` | `.artifacts/watchlist/` | `.artifacts/reporting/` |
| `make run-pipeline-modular` | All six commands in sequence | Chained | `.artifacts/*/` |

**Artifact files produced (cumulative per stage):**

| Directory | JSON files |
|-----------|------------|
| `.artifacts/news/` | `news.json` |
| `.artifacts/research/` | `news.json`, `research.json` |
| `.artifacts/technical/` | `news.json`, `research.json`, `technical.json` |
| `.artifacts/ranking/` | + `ranking.json` |
| `.artifacts/watchlist/` | + `watchlist.json` |
| `.artifacts/reporting/` | + `reporting.json` |

**Run full modular chain:**

```bash
make run-pipeline-modular
```

**Run one stage in isolation (after prerequisites):**

```bash
make run-news
make run-research    # requires run-news first
```

Requires `ENABLE_WORKFLOW_CLI=true` (default).

---

## 4. Agent-enabled dry-runs

Optional feature flags for testing agent layers without changing default production behavior.

| Make command | Environment overrides | Purpose |
|--------------|----------------------|---------|
| `make run-beneficiary-agent` | `ENABLE_BENEFICIARY_AGENT=true` | Sector taxonomy indirect beneficiary discovery |
| `make run-catalyst-verifier` | `ENABLE_CATALYST_VERIFIER=true` | Extra catalyst OTHER refinement pass |
| `make run-market-context` | `ENABLE_MARKET_CONTEXT=true`, `PREMARKET_STRATEGY=premarket_institutional_v4` | Market context bonus via V4 ranking strategy |

All three run the **full pipeline** in dry-run mode:

```bash
make run-beneficiary-agent
```

---

## 5. Evaluation

| Make command | CLI equivalent | Requirements |
|--------------|----------------|--------------|
| `make eval` | `evaluate-module --module all` | None |
| `make eval-beneficiary` | `evaluate-module --module beneficiary_discovery` | None |
| `make eval-ranking` | `evaluate-module --module ranking_quality` | None |
| `make eval-recommendations` | `evaluate-recommendations --date $(DATE)` | `ENABLE_DATABASE=true`, persisted recommendations |
| `make show-evaluation` | `show-evaluation --date $(DATE)` | `ENABLE_DATABASE=true`, prior `eval-recommendations` |
| `make backtest` | `backtest --from $(BACKTEST_FROM) --to $(BACKTEST_TO)` | Live market data, `GEMINI_API_KEY` for live LLM |
| `make backtest-dry` | `backtest ... --dry-run` | None |

**Examples:**

```bash
make eval
make eval-beneficiary
make eval-recommendations DATE=2026-06-05
make show-evaluation DATE=2026-06-05
make backtest-dry BACKTEST_FROM=2026-06-01 BACKTEST_TO=2026-06-05
```

Evaluation datasets live in `evaluation/datasets/`.

---

## 5b. Catalyst taxonomy admin

Requires `ENABLE_DATABASE=true` and `make docker-up` (or running Postgres).

| Make command | CLI equivalent | Description |
|--------------|----------------|-------------|
| `make list-pending-catalysts` | `list-pending-catalysts` | List pending LLM-discovered catalyst proposals |
| `make approve-catalyst ID=<uuid>` | `approve-catalyst <uuid>` | Promote pending catalyst to active taxonomy |
| `make reject-catalyst ID=<uuid>` | `reject-catalyst <uuid>` | Reject a pending catalyst proposal |

**Examples:**

```bash
make list-pending-catalysts
make approve-catalyst ID=d1b270e2-f3f2-4a13-895b-37474d43737b
make reject-catalyst ID=d1b270e2-f3f2-4a13-895b-37474d43737b
```

---

## 6. Docker

| Make command | Description |
|--------------|-------------|
| `make compose-check` | Verify Docker/Podman Compose is installed |
| `make docker-up` | Start Postgres container and run Alembic migrations |
| `make docker-down` | Stop and remove containers |

**Database URL behavior:**

- Inside Docker, the `migrate` service sets `DATABASE_URL=...@postgres:5432`. Alembic reads this via [`alembic/env.py`](../alembic/env.py) and overrides `alembic.ini`.
- On the host, `make migrate` uses `localhost:5432` from `alembic.ini` unless you export `DATABASE_URL`.
- The `app` service in `docker-compose.yml` overrides `.env`'s `localhost` with `@postgres:5432` — do not remove that override.

**Typical DB workflow:**

```bash
make docker-up
# set ENABLE_DATABASE=true in .env
make run
make eval-recommendations DATE=2026-06-05
```

---

## Common workflows

### Daily pre-market (live)

**Watchlist pipeline:**

```bash
cp .env.example .env   # add GEMINI_API_KEY or LLM_PROVIDER=ollama
make run-premarket
# or: make run SESSION=premarket
```

**Institutional research desk** (loads prior post-market memory):

```bash
# Ensure research desk vars in .env (see section 2b)
make research-desk-premarket
```

### Daily post-market (live)

```bash
make research-desk-postmarket
# or watchlist review: make run-postmarket
```

### Safe local validation

```bash
make setup
make test
make run-dry
```

### Debug ranking pipeline

```bash
make run-debug
```

### Test modular architecture end-to-end

```bash
make run-pipeline-modular
ls .artifacts/reporting/
```

### Test evaluation suite

```bash
make eval
```

### Test optional agents

```bash
make run-beneficiary-agent
make run-catalyst-verifier
make run-market-context
```

---

## Environment variables referenced by Make targets

| Variable | Default | Affects |
|----------|---------|---------|
| `GEMINI_API_KEY` | — | `make run`, `make backtest` |
| `ENABLE_DATABASE` | `false` | `make eval-recommendations`, `make show-evaluation` |
| `ENABLE_TELEGRAM` | `false` | Live `make run` notifications |
| `ENABLE_WORKFLOW_CLI` | `true` | Modular `run-*` workflow targets |
| `ENABLE_CHECKPOINTING` | `false` | `make run-resume` |
| `ENABLE_BENEFICIARY_AGENT` | `false` | Set by `make run-beneficiary-agent` |
| `ENABLE_CATALYST_VERIFIER` | `false` | Set by `make run-catalyst-verifier` |
| `ENABLE_MARKET_CONTEXT` | `false` | Set by `make run-market-context` |
| `ENABLE_RESEARCH_DESK` | `true` | `research-desk-postmarket`, `research-desk-premarket` |
| `LLM_PROVIDER` | `gemini` | `ollama` for local runs without Gemini key |
| `MARKET_MEMORY_PATH` | `market_memory` | Research desk persistence root |
| `RAG_EMBEDDING_MODEL` | `nomic-embed-text` | Research desk memory index embeddings |
| `DRY_RUN` | `false` | Overridden by `--dry-run` on CLI targets |
| `LOG_FORMAT` | `console` | Set `json` for structured logs |

See `.env.example` for the full list.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `command not found: make` | Install make (Xcode CLI tools on macOS) |
| `No module named pytest` | Run `make setup` first |
| `Configuration error: GEMINI_API_KEY` | Use `make run-dry`, set `LLM_PROVIDER=ollama`, or add Gemini key |
| Research desk fails on global/options | Try `NO_STRICT=1` for debugging; check NSE/Ollama connectivity |
| `nomic-embed-text` not found | `ollama pull nomic-embed-text` |
| `ENABLE_WORKFLOW_CLI=false` | Set `ENABLE_WORKFLOW_CLI=true` in `.env` |
| Modular step fails on missing input | Run prior step (e.g. `make run-news` before `make run-research`) |
| `eval-recommendations` fails | Enable DB, run `make docker-up`, run live job with `ENABLE_DATABASE=true` |
| Checkpoint resume fails | `pip install -e ".[checkpoint]"`, set `ENABLE_CHECKPOINTING=true` |

---

## Related documentation

- [USAGE_GUIDE.md](./USAGE_GUIDE.md) — scenario-based guide (which command when)
- [MODULAR_WORKFLOW_ARCHITECTURE.md](./MODULAR_WORKFLOW_ARCHITECTURE.md) — workflow modules and feature flags
- [RESEARCH_DESK_AUDIT.md](./RESEARCH_DESK_AUDIT.md) — institutional research desk agent audit
- [PREMARKET_PIPELINE_DIAGNOSTICS.md](./PREMARKET_PIPELINE_DIAGNOSTICS.md) — watchlist pipeline diagnostics
- [../README.md](../README.md) — project overview
- [../AI_TRADING_AGENT_FULL_SYSTEM_DOCUMENTATION.md](../AI_TRADING_AGENT_FULL_SYSTEM_DOCUMENTATION.md) — full system audit

---

## Quick command index

```
make help
make setup | install | lint | format | typecheck | test | test-cov | migrate
make run | run-dry | run-debug | run-resume | trace
make run-premarket | run-intraday | run-postmarket
make research-desk-postmarket | research-desk-premarket
make run-news | run-research | run-technical | run-ranking | run-watchlist | run-reporting
make run-pipeline-modular
make run-beneficiary-agent | run-catalyst-verifier | run-market-context
make eval | eval-beneficiary | eval-ranking | eval-recommendations | show-evaluation
make backtest | backtest-dry
make list-pending-catalysts | approve-catalyst | reject-catalyst
make ui | ui-install
make docker-up | docker-down | compose-check
```
