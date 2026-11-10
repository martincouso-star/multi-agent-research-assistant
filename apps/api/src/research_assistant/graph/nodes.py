import json

from langchain_core.runnables import RunnableConfig

from research_assistant.errors import ResearchError
from research_assistant.graph.normalize import (
    assign_sub_questions,
    check_citations,
    normalize_findings,
)
from research_assistant.graph.prompts import (
    CRITIC_SYSTEM,
    PLANNER_SYSTEM,
    RESEARCHER_SYSTEM,
    WRITER_SYSTEM,
)
from research_assistant.graph.state import ResearchState
from research_assistant.jsonutil import parse_json_object, strip_fences
from research_assistant.search.base import SearchResult


def planner_node(state: ResearchState, config: RunnableConfig) -> dict:
    llm = config["configurable"]["llm"]
    raw = llm.complete(
        system=PLANNER_SYSTEM,
        user=json.dumps({"question": state["question"]}),
    )
    try:
        parsed = parse_json_object(raw)
    except ValueError as exc:
        raise ResearchError(f"Planner returned invalid JSON: {exc}") from exc
    sub_questions = assign_sub_questions(parsed.get("sub_questions") or [])
    if len(sub_questions) < 2:
        raise ResearchError("Planner did not return at least two sub-questions.")
    rationale = str(parsed.get("rationale") or "").strip()
    return {
        "sub_questions": sub_questions,
        "trace": [
            {
                "node": "planner",
                "title": f"Planned {len(sub_questions)} sub-questions",
                "detail": rationale or "Split the question into searchable parts.",
                "items": [item["text"] for item in sub_questions],
            }
        ],
    }


def researcher_node(state: ResearchState, config: RunnableConfig) -> dict:
    llm = config["configurable"]["llm"]
    search = config["configurable"]["search"]
    max_results = int(config["configurable"].get("max_results", 3))
    sources = _collect_sources(state, search, max_results)
    if not sources:
        raise ResearchError("Search returned no sources for this question.")
    raw = llm.complete(
        system=RESEARCHER_SYSTEM,
        user=json.dumps(
            {
                "question": state["question"],
                "sub_questions": state["sub_questions"],
                "sources": sources,
            }
        ),
    )
    try:
        parsed = parse_json_object(raw)
    except ValueError as exc:
        raise ResearchError(f"Researcher returned invalid JSON: {exc}") from exc
    findings = normalize_findings(
        parsed.get("findings") or [],
        sources,
        state["sub_questions"],
    )
    if not findings:
        raise ResearchError("Researcher produced no cited findings.")
    return {
        "sources": sources,
        "findings": findings,
        "trace": [
            {
                "node": "researcher",
                "title": f"Gathered {len(sources)} sources",
                "detail": f"Wrote {len(findings)} cited findings from the retrieved sources.",
                "items": [source["title"] for source in sources],
            }
        ],
    }


def writer_node(state: ResearchState, config: RunnableConfig) -> dict:
    llm = config["configurable"]["llm"]
    critique = state.get("critique") or {}
    revising = bool(critique) and not critique.get("approved", True)
    revision_instructions = critique.get("revision_instructions", "") if revising else ""
    raw = llm.complete(
        system=WRITER_SYSTEM,
        user=json.dumps(
            {
                "question": state["question"],
                "sub_questions": state["sub_questions"],
                "sources": state["sources"],
                "findings": state["findings"],
                "revision_instructions": revision_instructions,
                "previous_report": state["report_markdown"] if revising else "",
            }
        ),
    )
    markdown = strip_fences(raw)
    if not markdown:
        raise ResearchError("Writer returned an empty brief.")
    update: dict = {
        "report_markdown": markdown,
        "trace": [
            {
                "node": "writer",
                "title": "Revised the brief" if revising else "Drafted the brief",
                "detail": revision_instructions or "Assembled a cited brief from the findings.",
                "items": [],
            }
        ],
    }
    if revising:
        update["revision_count"] = state["revision_count"] + 1
    return update


def critic_node(state: ResearchState, config: RunnableConfig) -> dict:
    llm = config["configurable"]["llm"]
    structural = check_citations(state["report_markdown"], state["sources"])
    raw = llm.complete(
        system=CRITIC_SYSTEM,
        user=json.dumps(
            {
                "question": state["question"],
                "sub_questions": state["sub_questions"],
                "sources": state["sources"],
                "findings": state["findings"],
                "report": state["report_markdown"],
                "structural_ok": structural["ok"],
                "structural_issues": structural["issues"],
            }
        ),
    )
    try:
        parsed = parse_json_object(raw)
    except ValueError as exc:
        raise ResearchError(f"Critic returned invalid JSON: {exc}") from exc
    issues = _string_list(parsed.get("issues"))
    structural_issues = structural["issues"]
    combined_issues = list(structural_issues) + [
        issue for issue in issues if issue not in structural_issues
    ]
    approved = bool(parsed.get("approved")) and structural["ok"]
    instructions = str(parsed.get("revision_instructions") or "").strip()
    if not approved and not instructions:
        instructions = " ".join(combined_issues) or "Revise the brief so claims stay cited."
    critique = {
        "approved": approved,
        "summary": str(parsed.get("summary") or "").strip(),
        "issues": combined_issues,
        "revision_instructions": "" if approved else instructions,
        "citation_score": structural["citation_score"],
    }
    title = "Approved the brief" if approved else "Requested a revision"
    return {
        "critique": critique,
        "trace": [
            {
                "node": "critic",
                "title": title,
                "detail": critique["summary"] or title,
                "items": critique["issues"],
            }
        ],
    }


def route_after_critic(state: ResearchState) -> str:
    critique = state.get("critique") or {}
    if critique.get("approved"):
        return "end"
    if state["revision_count"] >= state["max_revisions"]:
        return "end"
    return "writer"


def _collect_sources(state: ResearchState, search, max_results: int) -> list[dict]:
    collected: list[dict] = []
    seen_urls: set[str] = set()
    notes = state["notes"].strip()
    if notes:
        _append_source(
            collected,
            seen_urls,
            SearchResult(
                title="User-supplied notes",
                url="local://notes",
                snippet=notes[:2000],
                source_name="Local notes",
            ),
        )
    for sub_question in state["sub_questions"]:
        query = f"{sub_question['text']} {state['question']}".strip()
        for result in search.search(query, max_results=max_results):
            _append_source(collected, seen_urls, result)
    return collected


def _append_source(collected: list[dict], seen_urls: set[str], result: SearchResult) -> None:
    if result.url in seen_urls:
        return
    seen_urls.add(result.url)
    collected.append(
        {
            "id": f"src-{len(collected) + 1}",
            "citation_index": len(collected) + 1,
            "title": result.title,
            "url": result.url,
            "snippet": result.snippet,
            "origin": result.source_name,
        }
    )


def _string_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []
