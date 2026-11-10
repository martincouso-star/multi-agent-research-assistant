import json

from research_assistant.jsonutil import parse_json_object


class MockLLM:
    """Deterministic stand-in so the graph runs without an API key.

    Each graph node marks its system prompt with ``ROLE:``. The response is
    derived only from the JSON payload the node sends, so the same question
    always yields the same plan, findings, brief, and critique.
    """

    name = "mock"

    def complete(self, *, system: str, user: str) -> str:
        payload = _payload(user)
        if "ROLE: planner" in system:
            return json.dumps(_plan(payload))
        if "ROLE: researcher" in system:
            return json.dumps(_research(payload))
        if "ROLE: writer" in system:
            return _write(payload)
        if "ROLE: critic" in system:
            return json.dumps(_critique(payload))
        raise ValueError("MockLLM received a prompt without a known ROLE marker")


def _payload(user: str) -> dict:
    try:
        return parse_json_object(user)
    except ValueError:
        return {"text": user}


def _plan(payload: dict) -> dict:
    question = " ".join(str(payload.get("question") or "").split())
    focus = question if len(question) <= 72 else f"{question[:69].rstrip()}..."
    return {
        "rationale": f"Break this into concepts, then evidence and limitations: {focus}",
        "sub_questions": [
            "What are the core concepts?",
            "What evidence and limitations matter?",
        ],
    }


def _research(payload: dict) -> dict:
    sources = payload.get("sources") or []
    sub_questions = payload.get("sub_questions") or []
    findings = []
    for index, source in enumerate(sources):
        sub_question = sub_questions[index % len(sub_questions)] if sub_questions else {"id": ""}
        snippet = str(source.get("snippet") or "").strip()
        findings.append(
            {
                "sub_question_id": sub_question.get("id", ""),
                "claim": snippet,
                "source_ids": [source.get("id")],
                "excerpt": snippet[:400],
            }
        )
    return {"findings": findings}


def _write(payload: dict) -> str:
    sub_questions = payload.get("sub_questions") or []
    sources = payload.get("sources") or []
    findings = payload.get("findings") or []
    index_by_id = {source["id"]: source["citation_index"] for source in sources}
    lines = ["## Summary", ""]

    summary_parts: list[str] = []
    for finding in findings[:3]:
        marker = _marker(finding, index_by_id)
        claim = _lead(str(finding.get("claim") or ""))
        if claim:
            summary_parts.append(f"{claim} {marker}".strip())
    lines.append(" ".join(summary_parts) if summary_parts else "No findings were retrieved.")
    lines.extend(["", "## Detailed findings", ""])

    uncovered: list[str] = []
    for sub_question in sub_questions:
        related = [
            finding
            for finding in findings
            if finding.get("sub_question_id") == sub_question.get("id")
        ]
        if not related:
            uncovered.append(str(sub_question.get("text") or ""))
            continue
        lines.append(f"### {sub_question.get('text', '')}")
        for finding in related:
            marker = _marker(finding, index_by_id)
            lines.append(f"- {str(finding.get('claim') or '').strip()} {marker}".rstrip())
        lines.append("")

    revision = str(payload.get("revision_instructions") or "").strip()
    if revision:
        lines.extend(["## Revision notes", "", revision, ""])

    lines.extend(
        [
            "## Limitations",
            "",
            (
                "This brief only uses the sources retrieved for the run. "
                "In the default mock provider those sources are local corpus entries, "
                "not live web pages."
            ),
        ]
    )
    if any(uncovered):
        joined = "; ".join(text for text in uncovered if text)
        lines.extend(["", f"No retrieved source mapped directly onto: {joined}."])
    lines.extend(["", "## Sources", ""])
    for source in sources:
        lines.append(
            f"{source['citation_index']}. {source['title']} — {source['url']}"
        )
    lines.append("")
    return "\n".join(lines)


def _critique(payload: dict) -> dict:
    structural_ok = bool(payload.get("structural_ok"))
    if structural_ok:
        return {
            "approved": True,
            "summary": "Citations resolve to retrieved sources and the brief covers the plan.",
            "issues": [],
            "revision_instructions": "",
        }
    issues = payload.get("structural_issues") or ["The brief is not sufficiently cited."]
    return {
        "approved": False,
        "summary": "The brief needs another pass before it can be approved.",
        "issues": issues,
        "revision_instructions": (
            "Rewrite the brief so every claim uses a numeric citation "
            "that matches the source list."
        ),
    }


def _lead(text: str) -> str:
    cleaned = " ".join(text.split())
    for index, char in enumerate(cleaned):
        if char in ".!?" and index >= 40:
            return cleaned[: index + 1]
    return cleaned


def _marker(finding: dict, index_by_id: dict[str, int]) -> str:
    markers = []
    for source_id in finding.get("source_ids") or []:
        number = index_by_id.get(source_id)
        if number is not None:
            markers.append(f"[{number}]")
    return " ".join(markers)
