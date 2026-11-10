from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from research_assistant import __version__
from research_assistant.config import Settings, get_settings
from research_assistant.errors import ResearchError
from research_assistant.llm.factory import build_llm
from research_assistant.runner import encode_sse, iter_events, run_research
from research_assistant.schemas import HealthResponse, ResearchReportModel, ResearchRequest
from research_assistant.search.factory import build_search


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    llm = build_llm(settings)
    search = build_search(settings)
    app = FastAPI(
        title="Multi-Agent Research Assistant",
        version=__version__,
        summary="Plan a question, gather sources, write a cited brief, and critique it.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list or ["http://localhost:3000"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.settings = settings
    app.state.llm = llm
    app.state.search = search

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(
            status="ok",
            llm_provider=settings.llm_provider,
            search_provider=settings.search_provider,
            llm_model=_llm_model(settings),
            search_name=search.name,
        )

    @app.post("/api/research", response_model=ResearchReportModel)
    def research(body: ResearchRequest) -> ResearchReportModel:
        try:
            return run_research(
                question=body.question,
                notes=body.notes,
                llm=app.state.llm,
                search=app.state.search,
                settings=app.state.settings,
            )
        except ResearchError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/api/research/stream")
    def research_stream(body: ResearchRequest) -> StreamingResponse:
        def generate():
            try:
                for kind, payload in iter_events(
                    question=body.question,
                    notes=body.notes,
                    llm=app.state.llm,
                    search=app.state.search,
                    settings=app.state.settings,
                ):
                    yield encode_sse(kind, payload)
                yield encode_sse("done", {})
            except ResearchError as exc:
                yield encode_sse("error", {"detail": str(exc)})

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    return app


def _llm_model(settings: Settings) -> str:
    provider = settings.llm_provider.strip().lower()
    if provider == "openai":
        return settings.openai_model
    if provider == "anthropic":
        return settings.anthropic_model
    return "deterministic-mock"


app = create_app()
