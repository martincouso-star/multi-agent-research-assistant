import operator
from typing import Annotated, TypedDict


class TraceStep(TypedDict):
    node: str
    title: str
    detail: str
    items: list[str]


class ResearchState(TypedDict):
    question: str
    notes: str
    sub_questions: list[dict]
    sources: list[dict]
    findings: list[dict]
    report_markdown: str
    critique: dict | None
    revision_count: int
    max_revisions: int
    trace: Annotated[list[TraceStep], operator.add]
