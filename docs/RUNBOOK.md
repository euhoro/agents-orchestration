# Runbook

## Modes

The app supports two runtime modes:

- `demo`: deterministic local adapters, no external credentials required
- `live`: real eBay Browse API data, optional LLM-backed workflow planning

## Setup

Install dependencies:

```bash
uv sync
```

## Run Demo Mode

CLI:

```bash
uv run second-hand-agents find-opportunities --query "vintage lamp" --top 5
```

JSON output:

```bash
uv run second-hand-agents find-opportunities --query "pedestal table" --json
```

API:

```bash
uv run uvicorn second_hand_agents.api.app:app --reload
```

Sample request:

```bash
curl -X POST http://127.0.0.1:8000/opportunities/search \
  -H "content-type: application/json" \
  -d '{"query":"vintage lamp","top_k":5,"max_candidates":8}'
```

## Run Live Mode

Set credentials:

```bash
export SECOND_HAND_MODE=live
export SECOND_HAND_USE_LLM_AGENTS=true
export OPENAI_API_KEY=...
export SECOND_HAND_EBAY_CLIENT_ID=...
export SECOND_HAND_EBAY_CLIENT_SECRET=...
export SECOND_HAND_EBAY_ENVIRONMENT=production
```

Then run:

```bash
uv run second-hand-agents find-opportunities --query "vintage lamp" --top 5
```

Or start the API:

```bash
uv run uvicorn second_hand_agents.api.app:app --reload
```

## Debugging

Fast verification:

```bash
uv run pytest -q
uv run ruff check .
```

Live adapter verification without network:

```bash
uv run pytest tests/unit/test_live_ebay.py -q
```

Integration verification:

```bash
uv run pytest tests/integration/test_workflow.py -q
```

Useful debugging notes:

- `demo_mode` warning means the app is using the deterministic pipeline instead of active LLM execution.
- `live_comp_mode` warning means the current live implementation is using active eBay listings as directional comparables, not true sold comps.
- Use `--json` on the CLI to inspect the full response payload.
- Main orchestration lives in `src/second_hand_agents/services/workflow.py`.
- Live eBay integration lives in `src/second_hand_agents/adapters/live_ebay.py`.

## Presenter Notes

- Demo mode is best for presentations because output is stable.
- Live mode is best for showing real-data capability and real credentials integration.
- The current live mode proves the architecture with official external data, but resale confidence is intentionally conservative because comps are based on active listings.
