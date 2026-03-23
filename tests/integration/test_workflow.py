from fastapi.testclient import TestClient

from second_hand_agents.api.app import create_app
from second_hand_agents.schemas import OpportunitySearchRequest
from second_hand_agents.services import build_orchestrator


def test_orchestrator_returns_ranked_opportunities() -> None:
    orchestrator = build_orchestrator()
    response = orchestrator.search(
        OpportunitySearchRequest(query="vintage lamp", top_k=3, max_candidates=5)
    )

    assert response.opportunities
    assert response.opportunities[0].rank == 1
    assert response.opportunities[0].margin is not None
    assert response.warnings


def test_api_search_route_returns_response_schema() -> None:
    client = TestClient(create_app())
    payload = {"query": "pedestal table", "top_k": 2, "max_candidates": 4}

    response = client.post("/opportunities/search", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["request"]["query"] == "pedestal table"
    assert len(body["opportunities"]) <= 2
