from fastapi.testclient import TestClient

from research_assistant.config import Settings
from research_assistant.main import create_app

QUESTION = "How does LangGraph coordinate multiple agents compared with a single prompt?"


def _client() -> TestClient:
    app = create_app(Settings(llm_provider="mock", search_provider="mock", max_revisions=1))
    return TestClient(app)


def test_health() -> None:
    response = _client().get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["llm_provider"] == "mock"
    assert body["search_provider"] == "mock"
    assert body["llm_model"] == "deterministic-mock"


def test_research_endpoint_returns_sources_and_markdown() -> None:
    response = _client().post("/api/research", json={"question": QUESTION, "notes": ""})
    assert response.status_code == 200
    body = response.json()
    assert body["question"] == QUESTION
    assert body["critique"]["approved"] is True
    assert len(body["sources"]) >= 2
    assert "state" in body["markdown"].lower()
    assert body["trace"][0]["node"] == "planner"


def test_research_rejects_a_short_question() -> None:
    response = _client().post("/api/research", json={"question": "short"})
    assert response.status_code == 422


def test_stream_emits_steps_then_a_report() -> None:
    with _client().stream("POST", "/api/research/stream", json={"question": QUESTION}) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        body = "".join(response.iter_text())
    assert "event: step" in body
    assert "event: report" in body
    assert "event: done" in body
    assert "LangGraph" in body
