from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.table import Table

from second_hand_agents.config import get_settings
from second_hand_agents.schemas import OpportunitySearchRequest
from second_hand_agents.services import build_orchestrator

app = typer.Typer(no_args_is_help=True, help="Find second-hand sourcing opportunities.")
console = Console()


@app.callback()
def cli() -> None:
    """Second-hand sourcing demo CLI."""


@app.command("find-opportunities")
def find_opportunities(
    query: str = typer.Option(..., "--query", "-q", help="Search terms for the sourcing run."),
    top: int = typer.Option(5, "--top", min=1, max=25, help="Number of opportunities to show."),
    as_json: bool = typer.Option(False, "--json", help="Print structured JSON instead of a table."),
) -> None:
    settings = get_settings()
    orchestrator = build_orchestrator(settings)
    request = OpportunitySearchRequest(
        query=query, top_k=top, max_candidates=settings.max_candidates
    )
    response = orchestrator.search(request)

    if as_json:
        console.print_json(data=json.loads(response.model_dump_json()))
        return

    table = Table(title="Second-Hand Flip Opportunities", header_style="bold cyan")
    table.add_column("#", justify="right")
    table.add_column("Item")
    table.add_column("Buy", justify="right")
    table.add_column("Resale", justify="right")
    table.add_column("Profit", justify="right")
    table.add_column("Margin %", justify="right")
    table.add_column("Confidence", justify="right")

    for opportunity in response.opportunities:
        assert opportunity.margin is not None
        table.add_row(
            str(opportunity.rank),
            opportunity.item.normalized_title,
            f"${opportunity.margin.acquisition_cost:,.0f}",
            f"${opportunity.margin.expected_resale_price:,.0f}",
            f"${opportunity.margin.estimated_profit:,.0f}",
            f"{opportunity.margin.estimated_margin_pct * 100:.1f}%",
            f"{opportunity.margin.confidence * 100:.0f}%",
        )

    console.print(table)
    if response.warnings:
        console.print()
        for warning in response.warnings:
            console.print(f"[yellow]{warning.code}[/yellow]: {warning.message}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
