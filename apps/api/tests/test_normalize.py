from research_assistant.graph.normalize import (
    assign_sub_questions,
    check_citations,
    normalize_findings,
)


def test_assign_sub_questions_dedupes_and_caps() -> None:
    assigned = assign_sub_questions([" Alpha ", "Alpha", "Beta", "Gamma", "Delta", "Epsilon"])
    assert [item["id"] for item in assigned] == ["sq-1", "sq-2", "sq-3", "sq-4"]
    assert assigned[0]["text"] == "Alpha"


def test_normalize_findings_drops_unknown_sources_and_falls_back() -> None:
    sources = [
        {"id": "src-1", "snippet": "First snippet."},
        {"id": "src-2", "snippet": "Second snippet."},
    ]
    sub_questions = [{"id": "sq-1", "text": "Scope"}]
    cleaned = normalize_findings(
        [
            {"claim": "Kept", "source_ids": ["src-1", "missing"], "sub_question_id": "nope"},
            {"claim": "Dropped", "source_ids": ["missing"]},
        ],
        sources,
        sub_questions,
    )
    assert cleaned == [
        {
            "sub_question_id": "sq-1",
            "claim": "Kept",
            "source_ids": ["src-1"],
            "excerpt": "Kept",
        }
    ]

    fallback = normalize_findings(
        [{"claim": "Nope", "source_ids": ["missing"]}],
        sources,
        sub_questions,
    )
    assert [item["source_ids"] for item in fallback] == [["src-1"], ["src-2"]]


def test_check_citations_flags_missing_and_out_of_range_markers() -> None:
    sources = [{"id": "src-1"}, {"id": "src-2"}]
    empty = check_citations("Too short.", sources)
    assert empty["ok"] is False

    valid = check_citations(
        "A cited sentence that is long enough to count as a brief. [1] Another one. [2]",
        sources,
    )
    assert valid["ok"] is True
    assert valid["citation_score"] == 1

    broken = check_citations(
        "A cited sentence that is long enough to count as a brief. [1] [9]",
        sources,
    )
    assert broken["ok"] is False
    assert broken["citation_score"] == 0.5
