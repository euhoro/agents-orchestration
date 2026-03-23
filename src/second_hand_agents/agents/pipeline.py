from __future__ import annotations

from dataclasses import dataclass

from pydantic_ai import Agent

from second_hand_agents.config import Settings
from second_hand_agents.schemas import (
    CollectedListing,
    ComparableSale,
    ListingExtractionResult,
    MarginEstimate,
    NormalizedItem,
    ReviewDecision,
    WorkflowPlan,
)
from second_hand_agents.services.margin import estimate_margin
from second_hand_agents.services.normalization import normalize_listing


@dataclass
class AgentServices:
    settings: Settings


@dataclass
class AgentPipeline:
    manager: Agent[AgentServices, WorkflowPlan]
    collector: Agent[AgentServices, list[CollectedListing]]
    extractor: Agent[AgentServices, ListingExtractionResult]
    comp_researcher: Agent[AgentServices, list[ComparableSale]]
    margin_analyst: Agent[AgentServices, MarginEstimate]
    reviewer: Agent[AgentServices, ReviewDecision]


def build_agent_pipeline(settings: Settings) -> AgentPipeline:
    manager = Agent[AgentServices, WorkflowPlan](
        settings.model_name,
        deps_type=AgentServices,
        output_type=WorkflowPlan,
        defer_model_check=True,
        instructions=(
            "You are the workflow manager for a second-hand sourcing system. "
            "Rewrite the query, derive compact search terms, and keep the "
            "category focused on furniture, decor, or lighting. "
            "Call the build_plan tool and return its result."
        ),
    )

    @manager.tool_plain
    def build_plan(query: str, max_candidates: int) -> WorkflowPlan:
        terms = [token.strip().lower() for token in query.split() if token.strip()]
        return WorkflowPlan(
            rewritten_query=query.strip(),
            search_terms=terms,
            category_focus="furniture and decor",
            max_candidates=max_candidates,
            notes=["Prefer conservative margin ranking."],
        )

    collector = Agent[AgentServices, list[CollectedListing]](
        settings.model_name,
        deps_type=AgentServices,
        output_type=list[CollectedListing],
        defer_model_check=True,
        instructions=(
            "You collect candidate listings by calling the available tool. "
            "Return only the tool results."
        ),
    )

    extractor = Agent[AgentServices, ListingExtractionResult](
        settings.model_name,
        deps_type=AgentServices,
        output_type=ListingExtractionResult,
        defer_model_check=True,
        instructions=(
            "You normalize a second-hand listing into a structured extraction "
            "result. Use only facts present in the title or raw content. Do "
            "not invent dimensions, materials, or condition details. Prefer "
            "missing values over guessing and return only the typed result."
        ),
    )

    comp_researcher = Agent[AgentServices, list[ComparableSale]](
        settings.model_name,
        deps_type=AgentServices,
        output_type=list[ComparableSale],
        defer_model_check=True,
        instructions=(
            "You find comparable resale sales. Use the tool and return the comparable records."
        ),
    )

    margin_analyst = Agent[AgentServices, MarginEstimate](
        settings.model_name,
        deps_type=AgentServices,
        output_type=MarginEstimate,
        defer_model_check=True,
        instructions=(
            "You estimate conservative margin from comparable sales and "
            "listing costs. Use the tool and return its output."
        ),
    )

    reviewer = Agent[AgentServices, ReviewDecision](
        settings.model_name,
        deps_type=AgentServices,
        output_type=ReviewDecision,
        defer_model_check=True,
        instructions=(
            "You review a resale opportunity candidate. Approve only when the "
            "item details, comps, and margin estimate are coherent and "
            "plausible. Reject weak or unclear candidates with explicit "
            "reasons. Return only the typed result."
        ),
    )
    return AgentPipeline(
        manager=manager,
        collector=collector,
        extractor=extractor,
        comp_researcher=comp_researcher,
        margin_analyst=margin_analyst,
        reviewer=reviewer,
    )


def margin_from_services(
    item: NormalizedItem,
    comps: list[ComparableSale],
    settings: Settings,
) -> MarginEstimate | None:
    return estimate_margin(item, comps, settings)


def extract_from_services(listing: CollectedListing) -> NormalizedItem:
    return normalize_listing(listing)
