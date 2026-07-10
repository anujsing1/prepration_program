"""Shared market data helpers for research desk agents."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

import structlog

from morning_trading_agent.infrastructure.providers.market.yfinance_adapter import YFinanceMarketAdapter

# Yahoo Finance symbols for Indian and global benchmarks
INDEX_SYMBOLS: dict[str, str] = {
    "NIFTY": "^NSEI",
    "SENSEX": "^BSESN",
    "BANKNIFTY": "^NSEBANK",
    "MIDCAP": "NIFTY_MID_SELECT.NS",
    "SMALLCAP": "^CNXSC",
    "INDIA_VIX": "^INDIAVIX",
}

SECTOR_INDEX_SYMBOLS: dict[str, str] = {
    "Banking": "^NSEBANK",
    "IT": "^CNXIT",
    "Auto": "NIFTY_AUTO.NS",
    "Pharma": "NIFTY_PHARMA.NS",
    "FMCG": "NIFTY_FMCG.NS",
    "PSU": "NIFTY_PSE.NS",
    "Realty": "NIFTY_REALTY.NS",
    "Energy": "NIFTY_ENERGY.NS",
    "Metals": "^CNXMETAL",
    "Defence": "NIFTY_IND_DEFENCE.NS",
    "Infra": "NIFTY_INFRA.NS",
}

GLOBAL_SYMBOLS: dict[str, str] = {
    "US_SP500": "^GSPC",
    "US_NASDAQ": "^IXIC",
    "EUROPE_STOXX": "^STOXX50E",
    "JAPAN_NIKKEI": "^N225",
    "HONG_KONG": "^HSI",
    "DOLLAR_INDEX": "DX-Y.NYB",
    "US_10Y": "^TNX",
    "CRUDE_OIL": "CL=F",
    "GOLD": "GC=F",
}


@dataclass(frozen=True)
class IndexMetrics:
    """Computed index metrics."""

    symbol: str
    label: str
    last_close: float
    momentum_pct: float
    trend: str
    relative_volume: float


class MarketDataHelper:
    """Fetch and compute index metrics via yfinance."""

    def __init__(self, *, lookback_days: int = 60) -> None:
        self._adapter = YFinanceMarketAdapter()
        self._lookback_days = lookback_days
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def fetch_index_metrics(self, label: str, yahoo_symbol: str) -> IndexMetrics | None:
        try:
            series = await self._adapter.get_price_data(yahoo_symbol, lookback_days=self._lookback_days)
        except Exception as exc:
            self._logger.debug("index_fetch_failed", label=label, symbol=yahoo_symbol, error=str(exc))
            return None
        bars = series.bars
        if len(bars) < 5:
            return None
        closes = [bar.close for bar in bars]
        volumes = [bar.volume for bar in bars]
        last = closes[-1]
        prev_5 = closes[-6] if len(closes) >= 6 else closes[0]
        momentum = ((last - prev_5) / prev_5 * 100.0) if prev_5 else 0.0
        sma_20 = sum(closes[-20:]) / min(20, len(closes))
        trend = "bullish" if last > sma_20 and momentum > 0 else "bearish" if last < sma_20 else "neutral"
        avg_vol = sum(volumes[-20:]) / max(1, min(20, len(volumes)))
        rel_vol = volumes[-1] / avg_vol if avg_vol else 1.0
        return IndexMetrics(
            symbol=yahoo_symbol,
            label=label,
            last_close=round(last, 2),
            momentum_pct=round(momentum, 2),
            trend=trend,
            relative_volume=round(rel_vol, 2),
        )

    async def fetch_many(self, mapping: dict[str, str]) -> list[IndexMetrics]:
        tasks = [self.fetch_index_metrics(label, sym) for label, sym in mapping.items()]
        results = await asyncio.gather(*tasks)
        return [item for item in results if item is not None]
