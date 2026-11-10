import json
from collections.abc import Iterator

from research_assistant.config import Settings
from research_assistant.errors import ResearchError
from research_assistant.graph.builder import build_graph
from research_assistant.graph.state import ResearchState
from research_assistant.llm.base import LLMProvider
from research_assistant.schemas import ResearchReportModel
from research_assistant.search.base import SearchProvider

_GRAPH = None


def get_graph():
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = build_graph()
    return _GRAPH


def initial_state(question: str, notes: str, max_revisions: int) -> ResearchState:
    return {
        "question": question,
        "notes": notes,
        "sub_questions": [],
        "sources": [],
        "findings": [],
        "report_markdown": "",
        "critique": None,
        "revision_count": 0,
        "max_revisions": max_revisions,
        "trace": [],
    }


def run_research(
    *,
    question: str,
    notes: str,
    llm: LLMProvider,
    search: SearchProvider,
    settings: Settings,
) -> ResearchReportModel:
    final = None
    for state in iter_states(
        question=question, notes=notes, llm=llm, search=search, settings=settings
    ):
        final = state
    if final is None:
        raise ResearchError("Graph produced no state")
    return report_from_state(final, llm_name=llm.name, search_name=search.name)


def iter_states(
    *,
    question: str,
    notes: str,
    llm: LLMProvider,
    search: SearchProvider,
    settings: Settings,
) -> Iterator[ResearchState]:
    graph = get_graph()
    config = {
        "configurable": {
            "llm": llm,
            "search": search,
            "max_results": settings.search_results_per_query,
        }
    }
    yield from graph.stream(
        initial_state(question, notes, settings.max_revisions),
        config,
        stream_mode="values",
    )


def iter_events(
    *,
    question: str,
    notes: str,
    llm: LLMProvider,
    search: SearchProvider,
    settings: Settings,
) -> Iterator[tuple[str, dict]]:
    seen = 0
    final = None
    for state in iter_states(
        question=question,
        notes=notes,
        llm=llm,
        search=search,
        settings=settings,
    ):
        final = state
        trace = state["trace"]
        while seen < len(trace):
            yield "step", trace[seen]
            seen += 1
    if final is None:
        raise ResearchError("Graph produced no state")
    report = report_from_state(final, llm_name=llm.name, search_name=search.name)
    yield "report", report.model_dump()


def encode_sse(event: str, payload: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"


def report_from_state(
    state: ResearchState,
    *,
    llm_name: str,
    search_name: str,
) -> ResearchReportModel:
    critique = state.get("critique") or {
        "approved": False,
        "summary": "The critic did not run.",
        "issues": ["Missing critique."],
        "revision_instructions": "",
        "citation_score": 0.0,
    }
    return ResearchReportModel(
        question=state["question"],
        sub_questions=state["sub_questions"],
        sources=state["sources"],
        findings=state["findings"],
        markdown=state["report_markdown"],
        critique=critique,
        revision_count=state["revision_count"],
        trace=state["trace"],
        llm_provider=llm_name,
        search_provider=search_name,
    )
