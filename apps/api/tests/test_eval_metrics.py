from evals.metrics import citation_resolution, combined_score, topic_coverage


def test_topic_coverage_is_case_insensitive() -> None:
    score = topic_coverage(
        "Retrieval grounds the Generator.",
        ["retrieval", "generator", "missing"],
    )
    assert score == 2 / 3


def test_citation_resolution_counts_only_in_range_markers() -> None:
    result = citation_resolution("Claim [1]. Other claim [2]. Bad [4].", source_count=2)
    assert result["score"] == 2 / 3
    assert result["distinct_valid"] == 2
    assert combined_score(1.0, float(result["score"])) == (1 + 2 / 3) / 2
