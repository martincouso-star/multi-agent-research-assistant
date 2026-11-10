import hashlib
import re

from research_assistant.search.base import SearchResult

# Local corpus used by the default search provider. Snippets are written so a
# brief can quote them directly. They are not live web pages.
_CORPUS: list[dict[str, object]] = [
    {
        "keywords": ["retrieval-augmented", "rag"],
        "title": "Retrieval-augmented generation, in brief",
        "url": "mock://corpus/rag-overview",
        "snippet": (
            "Retrieval-augmented generation (RAG) pairs a retriever, which searches "
            "an external document collection, with a generator that writes the answer. "
            "Teams use it to ground responses in source text."
        ),
    },
    {
        "keywords": ["retrieval-augmented", "rag", "hallucination"],
        "title": "Why teams add retrieval before generation",
        "url": "mock://corpus/rag-why",
        "snippet": (
            "A generator that answers from model parameters alone can introduce a "
            "hallucination. Retrieval grounds the draft in passages a reader can "
            "open, which is why teams accept the extra lookup step."
        ),
    },
    {
        "keywords": ["langgraph"],
        "title": "LangGraph as a stateful agent graph",
        "url": "mock://corpus/langgraph-overview",
        "snippet": (
            "LangGraph models a workflow as a graph of nodes that read and write "
            "shared state. Control moves along edges, so a later node can see the "
            "plan, the sources, and any earlier draft."
        ),
    },
    {
        "keywords": ["langgraph", "single prompt"],
        "title": "A graph versus a single prompt",
        "url": "mock://corpus/langgraph-vs-prompt",
        "snippet": (
            "A single prompt asks one model call to plan, search, and write. "
            "A graph keeps those steps as separate nodes with explicit control "
            "over when each one runs, including a loop back to the writer."
        ),
    },
    {
        "keywords": ["server-sent events", "sse"],
        "title": "Streaming progress with server-sent events",
        "url": "mock://corpus/sse-overview",
        "snippet": (
            "Server-sent events let an API stream named events to a browser client "
            "over one HTTP response. A research API can push progress as each agent "
            "finishes instead of waiting for the full brief."
        ),
    },
    {
        "keywords": ["server-sent events", "streaming"],
        "title": "When a research API should stream",
        "url": "mock://corpus/sse-when",
        "snippet": (
            "Streaming is worth the open connection when a run has several slow "
            "steps and the client benefits from seeing progress early. The tradeoff "
            "is a longer-lived request that must handle a dropped connection."
        ),
    },
    {
        "keywords": ["citation", "citations", "citing"],
        "title": "Citing sources inside a research brief",
        "url": "mock://corpus/citations-overview",
        "snippet": (
            "A citation ties a claim to a source the reader can check. Numeric "
            "markers stay useful only when each one resolves to an entry that was "
            "actually retrieved for the question."
        ),
    },
    {
        "keywords": ["citation", "citations", "citing", "groundedness"],
        "title": "Limits of automated citation coverage",
        "url": "mock://corpus/citations-limits",
        "snippet": (
            "Citation coverage counts whether claims point at retrieved sources. "
            "It does not prove a source truly supports the claim, so a critic still "
            "has to read the excerpt next to the sentence."
        ),
    },
]


class MockSearch:
    """Keyword search over a fixed local corpus, with a deterministic fallback."""

    name = "mock"

    def search(self, query: str, *, max_results: int = 5) -> list[SearchResult]:
        ranked = _rank(query)
        if not ranked:
            return _fallback(query)[:max_results]
        return ranked[:max_results]


def _rank(query: str) -> list[SearchResult]:
    text = query.lower()
    scored: list[tuple[int, str, SearchResult]] = []
    for document in _CORPUS:
        keywords = document["keywords"]
        assert isinstance(keywords, list)
        score = sum(1 for keyword in keywords if _hit(str(keyword), text))
        if score <= 0:
            continue
        result = SearchResult(
            title=str(document["title"]),
            url=str(document["url"]),
            snippet=str(document["snippet"]),
            source_name="Mock corpus",
        )
        scored.append((score, result.url, result))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [item[2] for item in scored]


def _hit(keyword: str, text: str) -> bool:
    if len(keyword) <= 4 and " " not in keyword and "-" not in keyword:
        return re.search(rf"\b{re.escape(keyword)}\b", text) is not None
    return keyword in text


def _fallback(query: str) -> list[SearchResult]:
    digest = hashlib.sha256(query.encode("utf-8")).hexdigest()[:12]
    clipped = query.strip()
    if len(clipped) > 90:
        clipped = clipped[:87].rstrip() + "..."
    return [
        SearchResult(
            title=f"Mock briefing: {clipped}",
            url=f"mock://generated/{digest}",
            snippet=(
                "No corpus entry matched this query. This deterministic briefing "
                f"restates the question ({query.strip()}) and does not add outside facts."
            ),
            source_name="Mock corpus",
        ),
        SearchResult(
            title="How to read a mock-mode research brief",
            url="mock://corpus/mock-mode",
            snippet=(
                "Mock mode returns a fixed local corpus so the graph, citations, and "
                "evals run without API keys. Switch SEARCH_PROVIDER and LLM_PROVIDER "
                "when you want live retrieval and a hosted model."
            ),
            source_name="Mock corpus",
        ),
    ]
