# Research Desk Agent Audit

## BEFORE Refactor

| Agent | Status | Reason |
|-------|--------|--------|
| MarketStructureAgent | FAKE | yfinance-only; breadth 0; hardcoded `range_bound`/`neutral` |
| SectorRotationAgent | FAKE | yfinance proxies; fake institutional participation; empty leaders |
| InstitutionalFlowAgent | FAKE | No FII/DII API; `neutral`/`50%` defaults |
| GlobalMarketAgent | PARTIAL | yfinance real when available; heuristic thresholds |
| NewsIntelligenceAgent | PARTIAL | Real news; naive title symbol parsing (`QUOTE`, `NO`) |
| CorporateEventAgent | PARTIAL | Real articles; garbage symbols from title split |
| OptionsFlowAgent | FAKE | PCR 1.05/0.95 proxy; `None` support/resistance |
| StockDiscoveryAgent | PARTIAL | Unvalidated symbol aggregation |
| TechnicalAnalysisDeskAgent | FAKE | yfinance momentum only; score anchored at 50 |
| HistoricalContextAgent | PARTIAL | RAG wired; 0.5 probability when empty |
| PortfolioConstructionAgent | FAKE | Fallback scores 50/55 when missing |
| RiskManagementAgent | FAKE | Formulaic VaR from risk_score only |
| ExecutiveSummaryAgent | REAL | Synthesis only |
| MemoryRagAgent | REAL | JSON + embeddings persistence |

**Coverage:** ~25% real data agents  
**Institutional readiness:** Low

---

## AFTER Refactor

| Agent | Status | Data Sources |
|-------|--------|--------------|
| MarketStructureAgent | REAL | NSE `/api/allIndices`, bhavcopy A/D breadth |
| SectorRotationAgent | REAL | NSE sector indices; always assigns leaders/laggards |
| InstitutionalFlowAgent | REAL | NSE `/api/fiidiiTradeReact` |
| GlobalMarketAgent | REAL | yfinance global indices & commodities |
| NewsIntelligenceAgent | REAL | News providers + `CanonicalSymbolService` |
| CorporateEventAgent | REAL | Validated NSE symbols only; fails if none |
| OptionsFlowAgent | REAL | NSE `/api/option-chain-indices` PCR, max pain, OI S/R |
| StockDiscoveryAgent | REAL | NSE master-validated symbols only |
| TechnicalAnalysisDeskAgent | REAL | bhavcopy OHLCV + RSI/EMA/MACD/ADX |
| HistoricalContextAgent | REAL | Market memory RAG retrieval |
| ScoringAgent | REAL | Cross-agent normalized score components |
| PortfolioConstructionAgent | REAL | Weighted ranking from real scores only |
| RiskManagementAgent | REAL | VIX, global gap risk, OI range, exposure math |
| ExecutiveSummaryAgent | REAL | Report + agent health section |
| MemoryRagAgent | REAL | Structured JSON + embedding index |

**AgentHealth:** Every agent reports `used_real_data`, `confidence`, `records_processed`, `errors`.  
**Strict mode:** Live runs fail loudly when critical agents lack real data.  
**Observability:** `.artifacts/research_desk/*_agent_health.json`, `execution_graph.json`, `pipeline_metrics.json`

---

## Execution Graph (Postmarket)

```
MarketStructureAgent → nse_allIndices, bhavcopy
SectorRotationAgent → nse_allIndices
InstitutionalFlowAgent → nse_fiidiiTradeReact
GlobalMarketAgent → yfinance
OptionsFlowAgent → nse_option_chain
NewsIntelligenceAgent → news_providers, nse_security_master
CorporateEventAgent → articles + symbol validation
StockDiscoveryAgent → validated symbols
TechnicalAnalysisAgent → bhavcopy/yfinance OHLCV
HistoricalContextAgent → market_memory RAG
ScoringAgent → upstream scores
PortfolioConstructionAgent → ranked watchlists
RiskManagementAgent → exposure/VaR
ExecutiveSummaryAgent → report
MemoryRagAgent → persist + index
```

---

## Remaining Gaps (MEDIUM)

- Index futures OI buildup (needs NSE derivatives historical API)
- Stock-level F&O positioning
- Outcome validation loop (EOD scoring of predictions)
- LLM reasoning layer for regime classification (optional Phase 2)
- Chroma/Qdrant backend (currently in-memory cosine index)
