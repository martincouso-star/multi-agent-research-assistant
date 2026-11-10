import json

from research_assistant.config import Settings
from research_assistant.llm.mock import MockLLM
from research_assistant.runner import run_research
from research_assistant.search.mock import MockSearch

QUESTION = "What is retrieval-augmented generation and why do teams use it?"


def _settings(**overrides) -> Settings:
    base = {"llm_provider": "mock", "search_provider": "mock", "max_revisions": 1}
    base.update(overrides)
    return Settings(**base)


def test_mock_graph_returns_a_cited_brief() -> None:
    report = run_research(
        question=QUESTION,
        notes="Local note: RAG looks up passages before writing.",
        llm=MockLLM(),
        search=MockSearch(),
        settings=_settings(),
    )
    assert [step.node for step in report.trace] == [
        "planner",
        "researcher",
        "writer",
        "critic",
    ]
    assert len(report.sub_questions) == 2
    assert any(source.url == "local://notes" for source in report.sources)
    assert report.critique.approved is True
    assert report.critique.citation_score == 1
    assert report.revision_count == 0
    assert "[1]" in report.markdown
    assert "retriever" in report.markdown.lower()
    assert report.llm_provider == "mock"
    assert report.search_provider == "mock"


def test_critic_can_send_the_brief_back_to_the_writer() -> None:
    class FailOnce(MockLLM):
        def __init__(self) -> None:
            self.critic_calls = 0

        def complete(self, *, system: str, user: str) -> str:
            if "ROLE: critic" in system:
                self.critic_calls += 1
                if self.critic_calls == 1:
                    return json.dumps(
                        {
                            "approved": False,
                            "summary": "The limitations are too thin.",
                            "issues": ["Expand the limitations."],
                            "revision_instructions": (
                                "Expand the limitations section with the evidence gaps."
                            ),
                        }
                    )
            return super().complete(system=system, user=user)

    report = run_research(
        question=QUESTION,
        notes="",
        llm=FailOnce(),
        search=MockSearch(),
        settings=_settings(max_revisions=1),
    )
    assert report.revision_count == 1
    assert report.critique.approved is True
    assert "evidence gaps" in report.markdown
    assert [step.node for step in report.trace].count("writer") == 2
    assert [step.node for step in report.trace].count("critic") == 2


def test_revision_budget_stops_a_writer_that_never_cites() -> None:
    class UncitedWriter(MockLLM):
        def complete(self, *, system: str, user: str) -> str:
            if "ROLE: writer" in system:
                return (
                    "This brief intentionally omits citations so the critic must "
                    "reject it for missing markers."
                )
            return super().complete(system=system, user=user)

    report = run_research(
        question=QUESTION,
        notes="",
        llm=UncitedWriter(),
        search=MockSearch(),
        settings=_settings(max_revisions=1),
    )
    assert report.critique.approved is False
    assert report.revision_count == 1
    assert any("citation" in issue.lower() for issue in report.critique.issues)
