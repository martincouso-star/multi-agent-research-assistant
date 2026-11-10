from research_assistant.config import Settings
from research_assistant.errors import ProviderConfigError
from research_assistant.llm.base import LLMProvider
from research_assistant.llm.mock import MockLLM


def build_llm(settings: Settings) -> LLMProvider:
    provider = settings.llm_provider.strip().lower()
    if provider == "mock":
        return MockLLM()
    if provider == "openai":
        if not settings.openai_api_key.strip():
            raise ProviderConfigError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        from research_assistant.llm.openai_provider import OpenAIProvider

        return OpenAIProvider(api_key=settings.openai_api_key, model=settings.openai_model)
    if provider == "anthropic":
        if not settings.anthropic_api_key.strip():
            raise ProviderConfigError(
                "ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic"
            )
        from research_assistant.llm.anthropic_provider import AnthropicProvider

        return AnthropicProvider(
            api_key=settings.anthropic_api_key,
            model=settings.anthropic_model,
        )
    raise ProviderConfigError(
        f"Unknown LLM_PROVIDER '{settings.llm_provider}'. Use mock, openai, or anthropic."
    )
