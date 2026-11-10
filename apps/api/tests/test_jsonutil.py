import pytest

from research_assistant.jsonutil import parse_json_object, strip_fences


def test_parse_json_object_strips_fences() -> None:
    raw = '```json\n{"approved": true, "summary": "ok"}\n```'
    assert parse_json_object(raw)["approved"] is True


def test_parse_json_object_finds_embedded_object() -> None:
    raw = 'Here is the result:\n{"sub_questions": ["a", "b"]}\nThanks.'
    assert parse_json_object(raw)["sub_questions"] == ["a", "b"]


def test_parse_json_object_rejects_arrays() -> None:
    with pytest.raises(ValueError):
        parse_json_object("[1, 2, 3]")


def test_strip_fences_leaves_plain_markdown() -> None:
    text = "# Title\n\nA paragraph."
    assert strip_fences(text) == text
