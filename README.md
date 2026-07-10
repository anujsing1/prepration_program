# Morning Trading Agent

Production-grade pre-market watchlist generator for Indian stock market day traders.

This is a **research assistant**, not an auto-trading or prediction system. AI extracts information and summarizes reports; all ranking logic is deterministic Python code.

## Architecture

```mermaid
flowchart TB
    CLI[CLI app.py] --> UC[GenerateMorningWatchlistUseCase]
    UC --> Graph[LangGraph Workflow]
    Graph --> News[News Adapters]
    Graph --> LLM[Gemini Flash/Pro]
    Graph --> Market[NSE Market Data]
    Graph --> TA[Technical Analysis]
    Graph --> Rank[Ranking Strategy]
    Graph --> DB[PostgreSQL]
    Graph --> TG[Telegram]
```

### Clean Architecture Layers

| Layer | Purpose |
|---|---|
| `domain/` | Entities, value objects, repository interfaces |
| `application/` | Use cases, ranking, technical analysis, ports |
| `infrastructure/` | Adapters for DB, LLM, news, market, Telegram |
| `graph/` | LangGraph workflow with class-based nodes |
| `presentation/` | CLI entry point |
| `config/` | Settings, factories, DI container |

### AI Boundary Rule

- **Gemini Flash**: Extract stocks, analyze news sentiment
- **Gemini Pro**: Generate markdown report narrative
- **Python**: Technical scores, final ranking (never delegated to LLM)

## Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL 16+
- Gemini API key
- Telegram bot token (optional)

### Local Setup

```bash
cd morning-trading-agent
cp .env.example .env
# Edit .env with your API keys (optional for dry-run)

make setup        # creates .venv and installs dependencies
make run-dry      # run without Docker, DB, or Gemini API key
```

**Important:** Use the project virtualenv — do not run bare `python app.py` with system Python.

```bash
source .venv/bin/activate
python app.py run-morning-job --dry-run
# OR
make run-dry
```

### Docker (optional — requires Docker Compose)

Docker Compose plugin is required (`docker compose`, not bare `docker`).

```bash
make docker-up    # starts PostgreSQL + runs migrations
make run          # full run (needs GEMINI_API_KEY in .env)
```

If `make docker-up` fails with "unknown command: docker compose", install [Docker Desktop](https://www.docker.com/products/docker-desktop/) or run `brew install docker-compose`.

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL async connection URL | `postgresql+asyncpg://mta:mta@localhost:5432/morning_trading_agent` |
| `GEMINI_API_KEY` | Google Gemini API key | (required for LLM nodes) |
| `GEMINI_FLASH_MODEL` | Flash model name | `gemini-2.5-flash` |
| `GEMINI_PRO_MODEL` | Pro model name | `gemini-2.5-pro` |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | (only if `ENABLE_TELEGRAM=true`) |
| `TELEGRAM_CHAT_ID` | Telegram chat ID | (only if `ENABLE_TELEGRAM=true`) |
| `ENABLE_TELEGRAM` | Send report to Telegram | `false` (console output only) |
| `ENABLE_DATABASE` | Persist results to PostgreSQL | `false` |
| `MARKET_DATA_SOURCE` | `bhavcopy`, `yfinance`, or `hybrid` | `bhavcopy` |
| `RANKING_STRATEGY` | Deprecated; use session strategy env vars below | — |
| `TRADING_SESSION_MODE` | `AUTO`, `PRE_MARKET`, `INTRADAY`, or `POST_MARKET` | `AUTO` |
| `TRADING_SESSION_OVERRIDE` | Force session (testing) | empty |
| `FORCE_SESSION` | Simple session override alias (`PREMARKET`, `INTRADAY`, `POSTMARKET`) | empty |
| `PREMARKET_STRATEGY` / `INTRADAY_STRATEGY` / `POSTMARKET_STRATEGY` | Strategy per session | see `.env.example` |
| `MARKET_OPEN_TIME` / `MARKET_CLOSE_TIME` | NSE hours (HH:MM) | `09:15` / `15:30` |
| `MARKET_TIMEZONE` | Market timezone | `Asia/Kolkata` |
| `RUN_DATETIME_OVERRIDE` | Backtest/debug run time (ISO-8601) | empty |
| `NEWS_PROVIDERS` | Comma-separated providers | `moneycontrol,economic_times,google_news,nse_announcements` |
| `NEWS_FRESHNESS_HOURS` | Freshness filter window (hours) | `12` |
| `MIN_WATCHLIST_SIZE` / `MAX_WATCHLIST_SIZE` | Watchlist size bounds | `5` / `10` |
| `PRO_GATE_MIN_TECHNICAL_SCORE` / `PRO_GATE_MIN_CATALYST_SCORE` / `PRO_GATE_MIN_FINAL_SCORE` | Professional gate score floors | `40` / `50` / `45` |
| `PRO_GATE_MIN_TRADEABILITY_SCORE` / `PRO_GATE_MIN_FRESHNESS_SCORE` / `PRO_GATE_MIN_IMPACT_SCORE` | Gate tradability, freshness, impact floors | `50` / `70` / `55` |
| `WATCHLIST_RELAXATION_STEP` / `WATCHLIST_ALLOW_RELAXATION` | Gate threshold relaxation when pool is too small | `5` / `true` |
| `MIN_PRICE_INR` | Reject penny stocks below this price | `20` |
| `TOP_N_CANDIDATES` | Watchlist size | `10` |
| `DRY_RUN` | Offline demo mode (stub LLM/market, no DB/Telegram) | `false` |

## Running the Daily Job

```bash
# Default: live news + market data, results printed to console
make run

# Enable PostgreSQL (requires running postgres)
ENABLE_DATABASE=true make run

# Enable Telegram (requires bot token + chat id in .env)
ENABLE_TELEGRAM=true make run

# Offline demo mode (stub data, no external APIs)
python app.py run-morning-job --dry-run

# Specific date
python app.py run-morning-job --date 2026-06-03
```

### Cron Example (8:00 AM IST, weekdays)

```cron
30 2 * * 1-5 cd /path/to/morning-trading-agent && docker compose run --rm app run-morning-job
```

## Testing

```bash
make test       # run all tests
make test-cov   # with coverage (target: 80%+)
make lint       # ruff
make typecheck  # mypy
```

## Workflow

```
START → FetchNews → ExtractStocks → AnalyzeNews → TechnicalAnalysis
      → Ranking → GenerateWatchlist → PersistResults → SendTelegram → END
```

## Ranking Formula (Hybrid Strategy)

```
final_score = news_score × 0.30 + technical_score × 0.50 + confidence_score × 0.20
```

News score is normalized from sentiment (-10 to +10 → 0 to 100) in Python.

## Troubleshooting

| Issue | Solution |
|---|---|
| `ModuleNotFoundError: morning_trading_agent` | Run `make setup` then use `make run-dry` or `.venv/bin/python app.py` |
| `docker compose` not found | Install Docker Desktop or use `make run-dry` (no Docker needed) |
| `unknown shorthand flag: 'd'` | Your Docker lacks Compose — see above |
| `SSL: CERTIFICATE_VERIFY_FAILED` (news/httpx) | Fixed via `truststore` — run `make setup` |
| `curl: (60) SSL certificate` (yfinance) | Fixed via merged macOS CA bundle in `.cache/ca-bundle.pem` |
| yfinance `JSONDecodeError` / `unexpected character` | Yahoo returns HTML block pages for `.NS` tickers — use `MARKET_DATA_SOURCE=bhavcopy` (default) |
| Slow bhavcopy (many HTTP requests) | Fixed: daily CSV files are cached once per run, shared across all symbols |
| No market data | Verify symbol exists on NSE; yfinance uses `.NS` suffix |
| Gemini errors | Verify `GEMINI_API_KEY` and model names |
| Telegram fails | Check bot token, chat ID, and message length (max 4096 chars) |
| DB connection | Ensure PostgreSQL is running and `DATABASE_URL` is correct |

## Future Enhancements

- NSE/BSE official APIs
- Zerodha Kite / Upstox / Angel One integrations
- F&O open interest analysis
- Gap up/down scanners, volume shockers
- ORB/VWAP strategies
- Backtesting engine, paper trading, portfolio tracking
- Risk management and position sizing modules

## License

Proprietary — internal use.
