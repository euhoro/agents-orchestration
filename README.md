# Second-Hand Agents

Multi-agent demo project for sourcing curated second-hand furniture and decor, researching resale comps, and ranking opportunities by conservative estimated margin.

## Stack

- `uv` for project management
- `PydanticAI` for specialist-agent boundaries
- `FastAPI` for the HTTP surface
- `Typer` + `Rich` for a presentable CLI
- `pytest` + `ruff` for verification

## What ships in v1

- A clean CLI: `find-opportunities --query "mid century lamp"`
- A FastAPI endpoint: `POST /opportunities/search`
- Strong Pydantic schemas for every workflow stage
- Demo source/resale adapters with deterministic outputs
- A Mermaid workflow diagram in [docs/second_hand_agents_plan.mmd](/Users/eu/PycharmProjects/AgentsOrchestration/docs/second_hand_agents_plan.mmd)

The app defaults to a deterministic demo pipeline so it runs cleanly without external credentials. The project still includes a PydanticAI agent layer and can be extended to use live models and real marketplace adapters.

## Modes

- `demo` is the default and uses stable local fixture-style adapters.
- `live` uses real eBay Browse API data and can use the manager agent through your LLM credentials.

Environment variables for live mode:

```bash
export SECOND_HAND_MODE=live
export SECOND_HAND_USE_LLM_AGENTS=true
export OPENAI_API_KEY=...
export SECOND_HAND_EBAY_CLIENT_ID=...
export SECOND_HAND_EBAY_CLIENT_SECRET=...
export SECOND_HAND_EBAY_ENVIRONMENT=production
```

## Quickstart

```bash
uv sync
uv run second-hand-agents find-opportunities --query "vintage lamp"
uv run uvicorn second_hand_agents.api.app:app --reload
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

## Running the demo

CLI:

```bash
uv run second-hand-agents find-opportunities --query "vintage lamp" --top 5
uv run second-hand-agents find-opportunities --query "pedestal table" --json
```

API:

```bash
uv run uvicorn second_hand_agents.api.app:app --reload
```

Then call it with:

```bash
curl -X POST http://127.0.0.1:8000/opportunities/search \
  -H "content-type: application/json" \
  -d '{"query":"vintage lamp","top_k":5,"max_candidates":8}'
```

## Debugging

- Use `uv run pytest -q` to verify the workflow quickly.
- Use `uv run pytest tests/unit/test_live_ebay.py -q` to validate the live adapter layer without making network calls.
- Use `uv run pytest tests/integration/test_workflow.py -q` when you are changing orchestration or API behavior.
- Use `uv run ruff check .` to catch import, style, and basic correctness issues.
- Use `uv run second-hand-agents find-opportunities --query "vintage lamp" --json` to inspect the full structured response instead of the table.
- The default run mode is deterministic demo mode. If you see a `demo_mode` warning, that is expected and means the app is using stable local adapters rather than live LLM execution.
- In `live` mode, expect a `live_comp_mode` warning because the first implementation uses active eBay listings as directional comps rather than true sold comps.
- Main workflow code lives in [workflow.py](/Users/eu/PycharmProjects/AgentsOrchestration/src/second_hand_agents/services/workflow.py), normalization in [normalization.py](/Users/eu/PycharmProjects/AgentsOrchestration/src/second_hand_agents/services/normalization.py), and margin logic in [margin.py](/Users/eu/PycharmProjects/AgentsOrchestration/src/second_hand_agents/services/margin.py).

## Architecture

1. Workflow manager shapes the request.
2. Source collector gathers listing candidates.
3. Listing extractor normalizes item records.
4. Comp researcher finds resale benchmarks.
5. Margin analyst estimates conservative resale margin.
6. Reviewer/ranker orders viable flips by margin and confidence.

## Notes

- Region is US-only in v1.
- Categories are furniture, decor, and lighting.
- Ranking prioritizes conservative margin percentage, then profit, then confidence.
- `SECOND_HAND_USE_LLM_AGENTS=true` is reserved for a future live-agent path.
