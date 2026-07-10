"""Memory/RAG Agent — persist session to market memory."""

from __future__ import annotations

import structlog

from morning_trading_agent.agents.research_desk.base import ResearchDeskAgent
from morning_trading_agent.application.services.memory.market_memory_index import MarketMemoryIndex
from morning_trading_agent.application.services.memory.market_memory_store import MarketMemoryStore
from morning_trading_agent.application.services.rag.embedding_provider import EmbeddingProvider
from morning_trading_agent.domain.value_objects.agent_health import AgentHealth
from morning_trading_agent.domain.value_objects.market_memory import MarketMemoryDocument
from morning_trading_agent.domain.value_objects.research_desk import ResearchDeskSnapshot


class MemoryRagAgent(ResearchDeskAgent):
    """Persist structured memory and rebuild semantic index."""

    name = "memory_rag"
    strict = False

    def __init__(
        self,
        store: MarketMemoryStore,
        index: MarketMemoryIndex,
        embedder: EmbeddingProvider,
        *,
        persist: bool = True,
    ) -> None:
        self._store = store
        self._index = index
        self._embedder = embedder
        self._persist = persist
        self._logger = structlog.get_logger(self.__class__.__name__)

    async def run(self, snapshot: ResearchDeskSnapshot) -> ResearchDeskSnapshot:
        health = AgentHealth(agent=self.name, data_sources=["market_memory_store", "embedding_index"])
        if self._persist:
            clean = _snapshot_for_persistence(snapshot)
            document = MarketMemoryDocument.from_snapshot(clean)
            path = self._store.save(document)
            snapshot.metadata["memory_path"] = str(path)
        await self._index.rebuild(self._embedder)
        chunks = self._index.document_count
        snapshot.metadata["memory_index_size"] = chunks
        health.used_real_data = True
        health.records_processed = chunks
        health.confidence = 1.0 if chunks > 0 else 0.5
        self._logger.info("memory_rag_persisted", date=snapshot.session_date, chunks=chunks)
        return self._finalize_health(snapshot, health, outputs={"index_chunks": chunks})

    def load_previous(self, snapshot: ResearchDeskSnapshot) -> MarketMemoryDocument | None:
        return self._store.load_previous_trading_day(snapshot.session_date)


def _snapshot_for_persistence(snapshot: ResearchDeskSnapshot) -> ResearchDeskSnapshot:
    """Strip non-JSON metadata before memory persistence."""
    skip = {"_observability", "raw_articles", "prior_memory"}
    clean_meta = {
        k: v
        for k, v in snapshot.metadata.items()
        if k not in skip and not k.startswith("_")
    }
    return snapshot.model_copy(update={"metadata": clean_meta})
