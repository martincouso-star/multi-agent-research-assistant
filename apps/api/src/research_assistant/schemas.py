from pydantic import BaseModel, Field, field_validator


class ResearchRequest(BaseModel):
    question: str = Field(min_length=8, max_length=2000)
    notes: str = Field(default="", max_length=8000)

    @field_validator("question", "notes")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @field_validator("question")
    @classmethod
    def question_length(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Question must be at least 8 characters")
        return value


class SubQuestionModel(BaseModel):
    id: str
    text: str


class SourceModel(BaseModel):
    id: str
    citation_index: int
    title: str
    url: str
    snippet: str
    origin: str


class FindingModel(BaseModel):
    sub_question_id: str
    claim: str
    source_ids: list[str]
    excerpt: str


class TraceStepModel(BaseModel):
    node: str
    title: str
    detail: str
    items: list[str]


class CritiqueModel(BaseModel):
    approved: bool
    summary: str
    issues: list[str]
    revision_instructions: str
    citation_score: float


class ResearchReportModel(BaseModel):
    question: str
    sub_questions: list[SubQuestionModel]
    sources: list[SourceModel]
    findings: list[FindingModel]
    markdown: str
    critique: CritiqueModel
    revision_count: int
    trace: list[TraceStepModel]
    llm_provider: str
    search_provider: str


class HealthResponse(BaseModel):
    status: str
    llm_provider: str
    search_provider: str
    llm_model: str
    search_name: str
