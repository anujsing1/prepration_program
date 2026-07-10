"""LLM factory."""

from morning_trading_agent.application.adapters.ollama_adapter import OllamaAdapter
from morning_trading_agent.application.ports.providers import LLMProvider
from morning_trading_agent.config.settings import Settings
from morning_trading_agent.domain.exceptions.base import ConfigurationException
from morning_trading_agent.infrastructure.llm.gemini_adapter import GeminiAdapter
from morning_trading_agent.infrastructure.llm.stub_adapter import StubLLMProvider


class LLMFactory:
    """Creates LLM provider instances."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def create_llm_provider(self, *, allow_stub: bool = False) -> LLMProvider:
        """Create LLM adapter based on LLM_PROVIDER setting."""
        provider = self._settings.app.llm_provider
        if allow_stub or provider == "stub":
            return StubLLMProvider()

        cache_enabled = self._settings.app.llm_cache_enabled

        if provider == "ollama":
            return OllamaAdapter(
                self._settings.ollama,
                cache_enabled=cache_enabled,
            )

        if provider == "gemini":
            api_key = self._settings.gemini.gemini_api_key.strip()
            if not api_key:
                raise ConfigurationException(
                    "GEMINI_API_KEY is required when LLM_PROVIDER=gemini. "
                    "Use --dry-run or LLM_PROVIDER=ollama for offline/local mode."
                )
            return GeminiAdapter(
                self._settings.gemini,
                cache_enabled=cache_enabled,
            )

        raise ConfigurationException(
            f"Invalid LLM_PROVIDER={provider!r}. Expected gemini, ollama, or stub."
        )
