"""Run the golden question set through the configured research graph.

The pass/fail guard is enforced only for the default mock providers. Hosted
models are scored and printed, then left as an exploratory run.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "apps" / "api" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evals.metrics import citation_resolution, combined_score, topic_coverage  # noqa: E402

from research_assistant.config import Settings  # noqa: E402
from research_assistant.llm.factory import build_llm  # noqa: E402
from research_assistant.runner import run_research  # noqa: E402
from research_assistant.search.factory import build_search  # noqa: E402


def main() -> int:
    settings = Settings()
    llm = build_llm(settings)
    search = build_search(settings)
    cases = json.loads((ROOT / "evals" / "golden_questions.json").read_text(encoding="utf-8"))
    enforce_guard = (
        settings.llm_provider.strip().lower() == "mock"
        and settings.search_provider.strip().lower() == "mock"
    )

    print(
        f"provider={settings.llm_provider} search={settings.search_provider} "
        f"guard={'on' if enforce_guard else 'off (hosted run, scores only)'}"
    )
    header = f"{'id':<24} {'coverage':>8} {'citations':>10} {'score':>7} {'result':>8}"
    print(header)
    print("-" * len(header))

    failed = False
    for case in cases:
        report = run_research(
            question=case["question"],
            notes="",
            llm=llm,
            search=search,
            settings=settings,
        )
        coverage = topic_coverage(report.markdown, case["expected_topics"])
        citations = citation_resolution(report.markdown, len(report.sources))
        score = combined_score(coverage, float(citations["score"]))
        passed = True
        if enforce_guard:
            passed = (
                score >= float(case["min_score"])
                and float(citations["score"]) == 1.0
                and int(citations["distinct_valid"]) >= int(case["min_citations"])
            )
        if not passed:
            failed = True
        result = "pass" if passed else "fail"
        print(
            f"{case['id']:<24} {coverage:8.2f} {float(citations['score']):10.2f} "
            f"{score:7.2f} {result:>8}"
        )

    print()
    if enforce_guard:
        print("Guard thresholds are a regression check for the mock stack, not a benchmark.")
    else:
        print("Hosted providers are not compared with the mock guard.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
