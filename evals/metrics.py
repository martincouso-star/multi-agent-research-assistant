"""Small, explicit scores for the offline golden set.

These are regression checks for the harness. They are not a benchmark of a
hosted model, and they do not measure whether a source truly supports a claim.
"""

import re


def topic_coverage(markdown: str, topics: list[str]) -> float:
    """Fraction of topic strings that appear in the brief, case-insensitive."""
    if not topics:
        return 1.0
    text = markdown.lower()
    hits = sum(1 for topic in topics if topic.lower() in text)
    return hits / len(topics)


def citation_resolution(markdown: str, source_count: int) -> dict[str, float | int]:
    """How many numeric citation markers point at a retrieved source."""
    numbers = [int(value) for value in re.findall(r"\[(\d+)\]", markdown)]
    if not numbers or source_count <= 0:
        return {"score": 0.0, "distinct_valid": 0, "markers": 0}
    valid = [number for number in numbers if 1 <= number <= source_count]
    return {
        "score": len(valid) / len(numbers),
        "distinct_valid": len(set(valid)),
        "markers": len(numbers),
    }


def combined_score(coverage: float, citation_score: float) -> float:
    return 0.5 * coverage + 0.5 * citation_score
