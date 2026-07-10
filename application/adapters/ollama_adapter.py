"""Ollama LLM adapter using OpenAI-compatible API."""

from __future__ import annotations

import json
from typing import cast

import structlog
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from morning_trading_agent.application.ports.providers import LLMProvider
from morning_trading_agent.application.services.catalyst.catalyst_scoring_service import (
    CatalystScoringService,
)
from morning_trading_agent.application.services.catalyst.sentiment_analysis_mapper import (
    SentimentAnalysisMapper,
)
from morning_trading_agent.config.settings import OllamaSettings
from morning_trading_agent.domain.entities.article import (
    Article,
    ExtractedStock,
    SentimentAnalysis,
    Stock,
    TradingCandidate,
    Watchlist,
)
from morning_trading_agent.domain.entities.catalyst_taxonomy import CatalystTaxonomyEntry
from morning_trading_agent.domain.entities.llm_sentiment import (
    CatalystReclassificationRequest,
    CatalystReclassificationResult,
    CatalystReclassificationResultList,
    LLMSentimentAnalysisList,
)
from morning_trading_agent.domain.exceptions.base import LLMException
from morning_trading_agent.domain.value_objects.session_report_titles import (
    watchlist_report_title,
)
from morning_trading_agent.domain.value_objects.trading_session import TradingSessionMode
from morning_trading_agent.infrastructure.llm.llm_response_cache import LLMResponseCache
from morning_trading_agent.infrastructure.llm.prompts.templates import (
    EXTRACT_STOCKS_PROMPT,
    GENERATE_REPORT_PROMPT,
    RECLASSIFY_CATALYSTS_PROMPT,
    build_analyze_news_prompt,
)
from morning_trading_agent.infrastructure.llm.provider_generation_config import (
    ollama_generation_config,
    with_temperature,
)
from morning_trading_agent.infrastructure.llm.structured_llm_mixin import (
    ExtractedStockList,
    StructuredLLMMixin,
    classify_llm_error,
)


class OllamaAdapter(StructuredLLMMixin, LLMProvider):
    """Ollama provider via OpenAI-compatible /v1 chat completions."""

    @property
    def provider_name(self) -> str:
        return "OllamaAdapter"

    def __init__(
        self,
        settings: OllamaSettings,
        *,
        cache: LLMResponseCache | None = None,
        cache_enabled: bool = True,
        scoring_service: CatalystScoringService | None = None,
    ) -> None:
        self._settings = settings
        self._logger = structlog.get_logger(self.__class__.__name__)
        self._clients: dict[str, ChatOpenAI] = {}
        self._cache = cache or LLMResponseCache(enabled=cache_enabled)
        self._generation_config = ollama_generation_config(settings)
        scoring = scoring_service or CatalystScoringService()
        self._sentiment_mapper = SentimentAnalysisMapper(scoring_service=scoring)

    def _client_for(self, model_name: str, *, temperature: float) -> ChatOpenAI:
        config = with_temperature(self._generation_config, temperature)
        cache_key = f"{model_name}:{temperature}"
        if cache_key not in self._clients:
            client_kwargs: dict = {
                "model": model_name,
                "base_url": self._settings.ollama_base_url,
                "api_key": "ollama",
                "temperature": config.temperature,
                "timeout": config.timeout_seconds,
            }
            if config.extra_body:
                client_kwargs["extra_body"] = config.extra_body
            self._clients[cache_key] = ChatOpenAI(**client_kwargs)
        return self._clients[cache_key]

    async def extract_stocks(self, articles: list[Article]) -> list[ExtractedStock]:
        if not articles:
            return []
        prompt = EXTRACT_STOCKS_PROMPT.format(articles=self._format_articles(articles))
        cache_key = LLMResponseCache.cache_key("extract", prompt)
        cached = self._cache.get(cache_key, ExtractedStockList)
        if cached is not None:
            return cast(list[ExtractedStock], cached.stocks)
        model = self._client_for(self._settings.ollama_model, temperature=0.1)
        result = await self._invoke_structured(
            model,
            prompt,
            ExtractedStockList,
            model_name=self._settings.ollama_model,
            provider_name=self.provider_name,
            operation="extract_stocks",
        )
        wrapper = ExtractedStockList(stocks=cast(list[ExtractedStock], result))
        self._cache.set(cache_key, wrapper)
        return cast(list[ExtractedStock], result)

    async def analyze_news_llm(
        self,
        articles: list[Article],
        stocks: list[Stock],
        *,
        taxonomy: list[CatalystTaxonomyEntry] | None = None,
        symbol_article_map: dict[str, list] | None = None,
        rag_context: list[str] | None = None,
    ) -> list:
        _ = symbol_article_map
        if not stocks:
            return []
        prompt_template = build_analyze_news_prompt(taxonomy=taxonomy, rag_context=rag_context)
        prompt = prompt_template.format(
            stocks=self._format_stocks(stocks),
            articles=self._format_articles(articles),
        )
        cache_key = LLMResponseCache.cache_key("analyze", prompt)
        cached = self._cache.get(cache_key, LLMSentimentAnalysisList)
        if cached is not None:
            return list(cached.analyses)
        model = self._client_for(self._settings.ollama_model, temperature=0.1)
        llm_results = await self._invoke_structured(
            model,
            prompt,
            LLMSentimentAnalysisList,
            model_name=self._settings.ollama_model,
            provider_name=self.provider_name,
            operation="analyze_news_llm",
        )
        self._cache.set(cache_key, LLMSentimentAnalysisList(analyses=cast(list, llm_results)))
        return cast(list, llm_results)

    async def analyze_news(
        self,
        articles: list[Article],
        stocks: list[Stock],
        *,
        taxonomy: list[CatalystTaxonomyEntry] | None = None,
        symbol_article_map: dict[str, list] | None = None,
        rag_context: list[str] | None = None,
    ) -> list[SentimentAnalysis]:
        llm_results = await self.analyze_news_llm(
            articles,
            stocks,
            taxonomy=taxonomy,
            symbol_article_map=symbol_article_map,
            rag_context=rag_context,
        )
        return [self._sentiment_mapper.to_domain(item) for item in llm_results]

    async def reclassify_catalysts(
        self,
        requests: list[CatalystReclassificationRequest],
        *,
        taxonomy_codes: list[str] | None = None,
    ) -> list[CatalystReclassificationResult]:
        if not requests:
            return []
        codes = taxonomy_codes or []
        items = "\n".join(
            f"- symbol={item.symbol}; headline={item.headline}; summary={item.summary[:200]}"
            for item in requests
        )
        prompt = RECLASSIFY_CATALYSTS_PROMPT.format(
            taxonomy_codes=", ".join(codes[:120]),
            items=items,
        )
        cache_key = LLMResponseCache.cache_key("reclassify", prompt)
        cached = self._cache.get(cache_key, CatalystReclassificationResultList)
        if cached is not None:
            return list(cached.results)
        model = self._client_for(self._settings.ollama_model, temperature=0.0)
        results = await self._invoke_structured(
            model,
            prompt,
            CatalystReclassificationResultList,
            model_name=self._settings.ollama_model,
            provider_name=self.provider_name,
            operation="reclassify_catalysts",
        )
        wrapper = CatalystReclassificationResultList(results=cast(list, results))
        self._cache.set(cache_key, wrapper)
        return cast(list[CatalystReclassificationResult], results)

    async def generate_report(
        self, watchlist: Watchlist, candidates: list[TradingCandidate]
    ) -> str:
        session = (
            TradingSessionMode(watchlist.session_mode)
            if watchlist.session_mode
            else TradingSessionMode.PRE_MARKET
        )
        report_title = watchlist_report_title(session)
        data = {
            "strategy": watchlist.strategy,
            "run_date": watchlist.run_date.isoformat(),
            "candidates": [c.model_dump(mode="json") for c in candidates],
        }
        prompt = GENERATE_REPORT_PROMPT.format(
            report_title=report_title,
            watchlist_data=json.dumps(data, indent=2),
        )
        model = self._client_for(self._settings.ollama_model, temperature=0.3)
        config = with_temperature(self._generation_config, 0.3)
        try:
            self._logger.info(
                "llm_report_start",
                model=self._settings.ollama_model,
                provider=self.provider_name,
            )

            async def _call() -> str:
                response = await model.ainvoke([HumanMessage(content=prompt)])
                content = response.content
                if isinstance(content, str):
                    return content
                return str(content)

            return await self._invoke_with_retry(
                _call,
                model=self._settings.ollama_model,
                operation="generate_report",
                provider_name=self.provider_name,
                config=config,
            )
        except Exception as exc:
            raise LLMException(
                f"Report generation failed: {exc}",
                cause=exc,
                error_type=classify_llm_error(exc),
            ) from exc
