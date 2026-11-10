import httpx

from research_assistant.search.mock import MockSearch
from research_assistant.search.tavily import TavilySearch


def test_mock_search_is_deterministic_and_matches_corpus() -> None:
    search = MockSearch()
    query = "What is retrieval-augmented generation and why do teams use it?"
    first = search.search(query, max_results=3)
    second = search.search(query, max_results=3)
    assert [item.url for item in first] == [item.url for item in second]
    assert len(first) >= 2
    assert all(item.url.startswith("mock://corpus/rag-") for item in first)
    blob = " ".join(item.snippet for item in first).lower()
    assert "retriever" in blob
    assert "hallucinat" in blob


def test_mock_search_falls_back_when_nothing_matches() -> None:
    results = MockSearch().search("zzzz-unmatched-topic", max_results=2)
    assert len(results) == 2
    assert results[0].url.startswith("mock://generated/")
    assert results[1].url == "mock://corpus/mock-mode"


def test_tavily_search_maps_results() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "https://api.tavily.com/search"
        body = request.read()
        assert b"secret-key" in body
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "title": "Example",
                        "url": "https://example.com/a",
                        "content": "A short source passage.",
                    },
                    {"title": "Skip", "url": "", "content": "no url"},
                ]
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    results = TavilySearch(api_key="secret-key", client=client).search("rag", max_results=2)
    assert len(results) == 1
    assert results[0].source_name == "Tavily"
    assert results[0].url == "https://example.com/a"
