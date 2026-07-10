.PHONY: help install setup lint format typecheck test test-cov migrate \
	run run-dry run-debug run-resume debug-pipeline \
	run-premarket run-intraday run-postmarket \
	research-desk-postmarket research-desk-premarket \
	run-news run-research run-technical run-ranking run-watchlist run-reporting \
	run-pipeline-modular \
	run-beneficiary-agent run-catalyst-verifier run-market-context \
	eval eval-beneficiary eval-ranking eval-recommendations show-evaluation backtest backtest-dry \
	list-pending-catalysts approve-catalyst reject-catalyst \
	docker-up docker-down compose-check ui ui-install

PYTHON := .venv/bin/python
APP := $(PYTHON) app.py
UV := uv
ARTIFACTS := .artifacts
DATE ?= $(shell date +%Y-%m-%d)
THREAD_ID ?= $(DATE)_morning
BACKTEST_FROM ?= 2026-06-01
BACKTEST_TO ?= 2026-06-05

COMPOSE := $(shell \
	if docker compose version >/dev/null 2>&1; then echo "docker compose"; \
	elif command -v docker-compose >/dev/null 2>&1; then echo "docker-compose"; \
	elif podman compose version >/dev/null 2>&1; then echo "podman compose"; \
	else echo ""; fi)

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------

help:
	@echo "Morning Trading Agent — Make commands"
	@echo ""
	@echo "Setup & quality:"
	@echo "  make setup              Create venv and install dev dependencies"
	@echo "  make install            Alias for setup"
	@echo "  make lint               Ruff lint"
	@echo "  make format             Black + ruff fix"
	@echo "  make typecheck          Mypy"
	@echo "  make test               Run full pytest suite"
	@echo "  make test-cov           Run tests with coverage report"
	@echo "  make migrate            Alembic upgrade head"
	@echo ""
	@echo "Full pipeline:"
	@echo "  make run                Live morning job (needs GEMINI_API_KEY or LLM_PROVIDER=ollama)"
	@echo "  make run-dry            Offline dry-run (stub LLM/market, no DB/Telegram)"
	@echo "  make run-debug          Dry-run + ranking pipeline audit in output"
	@echo "  make trace              Trace one symbol lifecycle (SYMBOL=RELIANCE)"
	@echo "  make run-resume         Resume from checkpoint (needs ENABLE_CHECKPOINTING=true)"
	@echo "  make debug-pipeline     Run each pipeline stage independently with diagnostics"
	@echo "                          Override: make run-resume THREAD_ID=2026-06-05_morning"
	@echo ""
	@echo "Trading session (watchlist pipeline):"
	@echo "  make run-premarket      Pre-market watchlist job (DRY=1 for dry-run)"
	@echo "  make run-intraday       Intraday watchlist job (DRY=1 for dry-run)"
	@echo "  make run-postmarket     Post-market watchlist job (DRY=1 for dry-run)"
	@echo ""
	@echo "Institutional research desk (multi-agent RAG):"
	@echo "  make research-desk-postmarket   Post-market desk → builds market_memory/"
	@echo "  make research-desk-premarket    Pre-market desk → loads prior memory + thesis validation"
	@echo "                          Override: OUT=run_report/my.md  NO_STRICT=1  DRY=1  DATE=2026-07-03"
	@echo ""
	@echo "Modular workflows (dry-run, writes artifacts under .artifacts/):"
	@echo "  make run-news           News ingestion workflow only"
	@echo "  make run-research       Research workflow (needs: make run-news first for --input)"
	@echo "  make run-technical      Technical analysis workflow"
	@echo "  make run-ranking        Ranking workflow"
	@echo "  make run-watchlist      Watchlist filter/gate/select workflow"
	@echo "  make run-reporting      Report/persist/telegram workflow"
	@echo "  make run-pipeline-modular  Run all 6 workflows in sequence (dry-run)"
	@echo ""
	@echo "Agent-enabled dry-runs (optional feature flags):"
	@echo "  make run-beneficiary-agent   ENABLE_BENEFICIARY_AGENT=true"
	@echo "  make run-catalyst-verifier   ENABLE_CATALYST_VERIFIER=true"
	@echo "  make run-market-context      ENABLE_MARKET_CONTEXT=true + V4 strategy"
	@echo ""
	@echo "Evaluation:"
	@echo "  make eval               Run all evaluation modules"
	@echo "  make eval-beneficiary     Beneficiary discovery eval only"
	@echo "  make eval-ranking         Ranking quality eval only"
	@echo "  make eval-recommendations EOD returns (needs ENABLE_DATABASE=true)"
	@echo "                          Override: make eval-recommendations DATE=2026-06-05"
	@echo "  make show-evaluation    Show analytics for a trade date (needs DB)"
	@echo "                          Override: make show-evaluation DATE=2026-06-05"
	@echo "  make backtest           Backtest date range (live market data)"
	@echo "                          Override: make backtest BACKTEST_FROM=2026-06-01 BACKTEST_TO=2026-06-05"
	@echo "  make backtest-dry       Backtest dry-run over date range"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up          Start Postgres + run migrations"
	@echo "  make docker-down        Stop containers"
	@echo ""
	@echo "Full reference: docs/MAKEFILE_REFERENCE.md"

# ---------------------------------------------------------------------------
# Setup & quality
# ---------------------------------------------------------------------------

setup:
	$(UV) python install 3.12
	$(UV) venv --python 3.12 .venv
	$(UV) pip install -e ".[dev]"
	@echo ""
	@echo "Setup complete. Activate with: source .venv/bin/activate"
	@echo "Then run: make run-dry"

install: setup

lint:
	.venv/bin/ruff check src tests

format:
	.venv/bin/black src tests
	.venv/bin/ruff check --fix src tests

typecheck:
	.venv/bin/mypy src

test:
	.venv/bin/pytest tests/ -v

test-cov:
	.venv/bin/pytest tests/ -v --cov=morning_trading_agent --cov-report=term-missing

migrate:
	.venv/bin/alembic upgrade head

# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------

run:
	$(APP) run-morning-job $(if $(SESSION),--session $(SESSION),) $(if $(AT),--at "$(AT)",)

run-dry:
	$(APP) run-morning-job --dry-run $(if $(SESSION),--session $(SESSION),) $(if $(AT),--at "$(AT)",)

run-premarket:
	$(APP) run-morning-job --session premarket $(if $(DRY),--dry-run,)

run-intraday:
	$(APP) run-morning-job --session intraday $(if $(DRY),--dry-run,)

run-postmarket:
	$(APP) run-morning-job --session postmarket $(if $(DRY),--dry-run,)

research-desk-postmarket:
	@mkdir -p run_report
	$(APP) run-research-desk --mode postmarket --session postmarket \
		$(if $(DRY),--dry-run,) \
		$(if $(NO_STRICT),--no-strict,) \
		$(if $(DATE),--date $(DATE),) \
		--output "$(if $(OUT),$(OUT),run_report/research_desk_postmarket_$(DATE).md)"

research-desk-premarket:
	@mkdir -p run_report
	$(APP) run-research-desk --mode premarket --session premarket \
		$(if $(DRY),--dry-run,) \
		$(if $(NO_STRICT),--no-strict,) \
		$(if $(DATE),--date $(DATE),) \
		--output "$(if $(OUT),$(OUT),run_report/research_desk_premarket_$(DATE).md)"

run-debug:
	$(APP) run-morning-job --dry-run --debug-ranking

trace:
	@test -n "$(SYMBOL)" || (echo "Usage: make trace SYMBOL=RELIANCE [FRESH=1] [DRY=1]"; exit 1)
	$(APP) trace-candidate --symbol $(SYMBOL) \
		$(if $(FRESH),--fresh,) \
		$(if $(DRY),--dry-run,)

run-resume:
	$(APP) run-morning-job --resume --thread-id $(THREAD_ID)

debug-pipeline:
	@mkdir -p $(ARTIFACTS)/debug
	$(APP) debug-pipeline --dry-run --output $(ARTIFACTS)/debug

# ---------------------------------------------------------------------------
# Modular workflows (dry-run + artifacts)
# ---------------------------------------------------------------------------

run-news:
	@mkdir -p $(ARTIFACTS)/news
	$(APP) run-news-workflow --dry-run --output $(ARTIFACTS)/news

run-research:
	@mkdir -p $(ARTIFACTS)/research
	$(APP) run-research-workflow --dry-run --input $(ARTIFACTS)/news --output $(ARTIFACTS)/research

run-technical:
	@mkdir -p $(ARTIFACTS)/technical
	$(APP) run-technical-workflow --dry-run --input $(ARTIFACTS)/research --output $(ARTIFACTS)/technical

run-ranking:
	@mkdir -p $(ARTIFACTS)/ranking
	$(APP) run-ranking-workflow --dry-run --input $(ARTIFACTS)/technical --output $(ARTIFACTS)/ranking

run-watchlist:
	@mkdir -p $(ARTIFACTS)/watchlist
	$(APP) run-watchlist-workflow --dry-run --input $(ARTIFACTS)/ranking --output $(ARTIFACTS)/watchlist

run-reporting:
	@mkdir -p $(ARTIFACTS)/reporting
	$(APP) run-reporting-workflow --dry-run --input $(ARTIFACTS)/watchlist --output $(ARTIFACTS)/reporting

run-pipeline-modular: run-news run-research run-technical run-ranking run-watchlist run-reporting
	@echo "Modular pipeline complete. Artifacts in $(ARTIFACTS)/"

# ---------------------------------------------------------------------------
# Agent-enabled runs (dry-run)
# ---------------------------------------------------------------------------

run-beneficiary-agent:
	ENABLE_BENEFICIARY_AGENT=true $(APP) run-morning-job --dry-run

run-catalyst-verifier:
	ENABLE_CATALYST_VERIFIER=true $(APP) run-morning-job --dry-run

run-market-context:
	ENABLE_MARKET_CONTEXT=true PREMARKET_STRATEGY=premarket_institutional_v4 $(APP) run-morning-job --dry-run

# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

eval:
	$(APP) evaluate-module --module all

eval-beneficiary:
	$(APP) evaluate-module --module beneficiary_discovery

eval-ranking:
	$(APP) evaluate-module --module ranking_quality

eval-recommendations:
	$(APP) evaluate-recommendations --date $(DATE)

show-evaluation:
	$(APP) show-evaluation --date $(DATE)

backtest:
	$(APP) backtest --from $(BACKTEST_FROM) --to $(BACKTEST_TO)

backtest-dry:
	$(APP) backtest --from $(BACKTEST_FROM) --to $(BACKTEST_TO) --dry-run

list-pending-catalysts:
	$(APP) list-pending-catalysts

approve-catalyst:
	@test -n "$(ID)" || (echo "Usage: make approve-catalyst ID=<pending-uuid>"; exit 1)
	$(APP) approve-catalyst $(ID)

reject-catalyst:
	@test -n "$(ID)" || (echo "Usage: make reject-catalyst ID=<pending-uuid>"; exit 1)
	$(APP) reject-catalyst $(ID)

# ---------------------------------------------------------------------------
# Workflow Studio (Streamlit UI)
# ---------------------------------------------------------------------------

ui-install:
	$(UV) pip install -e ".[ui]"

ui:
	$(PYTHON) -m streamlit run streamlit_app.py --server.headless true

# ---------------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------------

compose-check:
	@if [ -z "$(COMPOSE)" ]; then \
		echo "ERROR: No container compose command found."; \
		echo "Install one of:"; \
		echo "  - Docker Desktop (includes 'docker compose')"; \
		echo "  - brew install docker-compose"; \
		echo "  - Or run locally without Docker: make setup && make run-dry"; \
		exit 1; \
	fi

docker-up: compose-check
	$(COMPOSE) up -d postgres
	$(COMPOSE) --profile migrate run --rm --build migrate

docker-down: compose-check
	$(COMPOSE) down
