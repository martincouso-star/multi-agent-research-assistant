import httpx

from research_assistant.errors import ResearchError
from research_assistant.search.base import SearchResult


class TavilySearch:
    """Optional live web search via the Tavily API."""

    name = "tavily"

    def __init__(self, *, api_key: str, client: httpx.Client | None = None) -> None:
        self.api_key = api_key
        self._client = client or httpx.Client(timeout=30.0)
        self._owns_client = client is None

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def search(self, query: str, *, max_results: int = 5) -> list[SearchResult]:
        try:
            response = self._client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": self.api_key,
                    "query": query,
                    "max_results": max_results,
                    "include_answer": False,
                },
            )
            response.raise_for_status()
            body = response.json()
        except httpx.HTTPError as exc:
            raise ResearchError(
                f"Tavily search failed ({exc.__class__.__name__})"
            ) from exc
        results = []
        for item in body.get("results") or []:
            url = str(item.get("url") or "").strip()
            snippet = str(item.get("content") or "").strip()
            title = str(item.get("title") or url or "Untitled").strip()
            if not url or not snippet:
                continue
            results.append(
                SearchResult(
                    title=title,
                    url=url,
                    snippet=snippet,
                    source_name="Tavily",
                )
            )
        return results
