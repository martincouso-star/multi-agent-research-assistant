from research_assistant.config import Settings
from research_assistant.errors import ProviderConfigError
from research_assistant.search.base import SearchProvider
from research_assistant.search.mock import MockSearch


def build_search(settings: Settings) -> SearchProvider:
    provider = settings.search_provider.strip().lower()
    if provider == "mock":
        return MockSearch()
    if provider == "tavily":
        if not settings.tavily_api_key.strip():
            raise ProviderConfigError("TAVILY_API_KEY is required when SEARCH_PROVIDER=tavily")
        from research_assistant.search.tavily import TavilySearch

        return TavilySearch(api_key=settings.tavily_api_key)
    raise ProviderConfigError(
        f"Unknown SEARCH_PROVIDER '{settings.search_provider}'. Use mock or tavily."
    )
