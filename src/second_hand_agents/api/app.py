from __future__ import annotations

from typing import Annotated

from fastapi import Depends, FastAPI

from second_hand_agents.config import Settings, get_settings
from second_hand_agents.schemas import OpportunitySearchRequest, OpportunitySearchResponse
from second_hand_agents.services import WorkflowOrchestrator, build_orchestrator


def get_orchestrator(
    settings: Annotated[Settings, Depends(get_settings)],
) -> WorkflowOrchestrator:
    return build_orchestrator(settings)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Second-Hand Agents",
        summary="Multi-agent demo for sourcing second-hand flips with conservative margin ranking.",
        version="0.1.0",
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/opportunities/search", response_model=OpportunitySearchResponse)
    def search_opportunities(
        request: OpportunitySearchRequest,
        orchestrator: Annotated[WorkflowOrchestrator, Depends(get_orchestrator)],
    ) -> OpportunitySearchResponse:
        return orchestrator.search(request)

    return app


app = create_app()
