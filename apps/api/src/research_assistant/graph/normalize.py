import re


def assign_sub_questions(raw_items: list) -> list[dict]:
    questions: list[str] = []
    for item in raw_items:
        text = str(item).strip()
        if text and text not in questions:
            questions.append(text)
    questions = questions[:4]
    return [{"id": f"sq-{index}", "text": text} for index, text in enumerate(questions, start=1)]


def normalize_findings(
    raw_findings: list,
    sources: list[dict],
    sub_questions: list[dict],
) -> list[dict]:
    valid_ids = {source["id"] for source in sources}
    valid_sub_questions = {item["id"] for item in sub_questions}
    default_sub_question = sub_questions[0]["id"] if sub_questions else ""
    cleaned: list[dict] = []
    for item in raw_findings:
        if not isinstance(item, dict):
            continue
        claim = str(item.get("claim") or "").strip()
        raw_ids = item.get("source_ids") or []
        source_ids = [source_id for source_id in raw_ids if source_id in valid_ids]
        if not claim or not source_ids:
            continue
        sub_question_id = item.get("sub_question_id")
        if sub_question_id not in valid_sub_questions:
            sub_question_id = default_sub_question
        excerpt = str(item.get("excerpt") or claim).strip()[:400]
        cleaned.append(
            {
                "sub_question_id": sub_question_id,
                "claim": claim,
                "source_ids": source_ids,
                "excerpt": excerpt,
            }
        )
    if cleaned:
        return cleaned
    return _findings_from_sources(sources, sub_questions)


def _findings_from_sources(sources: list[dict], sub_questions: list[dict]) -> list[dict]:
    findings = []
    for index, source in enumerate(sources):
        sub_question_id = ""
        if sub_questions:
            sub_question_id = sub_questions[index % len(sub_questions)]["id"]
        snippet = str(source.get("snippet") or "").strip()
        findings.append(
            {
                "sub_question_id": sub_question_id,
                "claim": snippet,
                "source_ids": [source["id"]],
                "excerpt": snippet[:400],
            }
        )
    return findings


def check_citations(markdown: str, sources: list[dict]) -> dict:
    issues: list[str] = []
    if len(markdown.strip()) < 40:
        issues.append("Report is empty or too short.")
    numbers = [int(value) for value in re.findall(r"\[(\d+)\]", markdown)]
    if not numbers:
        issues.append("Report has no numeric citations.")
    source_count = len(sources)
    out_of_range = sorted({number for number in numbers if number < 1 or number > source_count})
    if out_of_range:
        issues.append(f"Citations out of range: {out_of_range}.")
    score = 0.0
    if numbers:
        valid = sum(1 for number in numbers if 1 <= number <= source_count)
        score = valid / len(numbers)
    return {"ok": not issues, "issues": issues, "citation_score": score}
