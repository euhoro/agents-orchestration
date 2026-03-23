from __future__ import annotations

import os
from dataclasses import dataclass

from second_hand_agents.adapters import (
    DemoResaleAdapter,
    DemoSourceAdapter,
    EbayBrowseClient,
    EbayResaleAdapter,
    EbaySourceAdapter,
)
from second_hand_agents.agents import AgentPipeline, AgentServices, build_agent_pipeline
from second_hand_agents.config import Settings, get_settings
from second_hand_agents.schemas import (
    CollectedListing,
    ListingExtractionResult,
    NormalizedItem,
    Opportunity,
    OpportunitySearchRequest,
    OpportunitySearchResponse,
    RunWarning,
    WorkflowPlan,
)
from second_hand_agents.services.margin import estimate_margin
from second_hand_agents.services.normalization import normalize_listing
from second_hand_agents.services.ranking import dedupe_and_rank


@dataclass
class WorkflowOrchestrator:
    settings: Settings
    source_adapter: DemoSourceAdapter | EbaySourceAdapter
    resale_adapter: DemoResaleAdapter | EbayResaleAdapter
    agent_pipeline: AgentPipeline | None = None

    def search(self, request: OpportunitySearchRequest) -> OpportunitySearchResponse:
        warnings: list[RunWarning] = []
        plan = self._build_plan(request)
        listings = self.source_adapter.search(plan.rewritten_query, plan.max_candidates)
        opportunities: list[Opportunity] = []

        for listing in listings:
            item = self._extract_item(listing, warnings)
            comps = self.resale_adapter.find_comps(item)
            margin = estimate_margin(item, comps, self.settings)
            opportunity = Opportunity(item=item, comps=comps, margin=margin)
            opportunities.append(self._review_opportunity(opportunity, warnings))

        accepted, rejected = dedupe_and_rank(opportunities)
        if self.settings.mode == "live":
            warnings.append(
                RunWarning(
                    code="live_comp_mode",
                    message=(
                        "Live mode currently uses active listing comparables from eBay Browse API, "
                        "not true sold comps, so confidence should be treated as directional."
                    ),
                )
            )
        if not self.agent_pipeline:
            warnings.append(
                RunWarning(
                    code="demo_mode",
                    message=(
                        "LLM agents are disabled or unavailable. The app is "
                        "running the deterministic pipeline with the same "
                        "agent boundaries."
                    ),
                )
            )
        return OpportunitySearchResponse(
            request=request,
            opportunities=accepted[: request.top_k],
            rejected=rejected,
            warnings=warnings,
        )

    def _extract_item(
        self,
        listing: CollectedListing,
        warnings: list[RunWarning],
    ) -> NormalizedItem:
        if self.settings.mode == "live" and self.agent_pipeline:
            try:
                result = self.agent_pipeline.extractor.run_sync(
                    (
                        "Extract structured item data from this listing.\n"
                        f"Title: {listing.title}\n"
                        f"Marketplace: {listing.source_marketplace}\n"
                        f"Location: {listing.location}\n"
                        f"Raw content: {listing.raw_content}\n"
                        "Return only the typed extraction result."
                    ),
                    deps=AgentServices(settings=self.settings),
                )
                return self._normalized_item_from_extraction(listing, result.output)
            except Exception:
                warnings.append(
                    RunWarning(
                        code="llm_extraction_fallback",
                        message=(
                            f"Fell back to deterministic extraction for listing "
                            f"{listing.listing_id} after LLM extraction failed."
                        ),
                    )
                )
        return normalize_listing(listing)

    def _review_opportunity(
        self,
        opportunity: Opportunity,
        warnings: list[RunWarning],
    ) -> Opportunity:
        if self.settings.mode != "live" or not self.agent_pipeline:
            return opportunity
        if opportunity.margin is None:
            return opportunity
        try:
            result = self.agent_pipeline.reviewer.run_sync(
                (
                    "Review this second-hand resale candidate. Approve only "
                    "when item details, comps, and margin are coherent.\n"
                    f"Item: {opportunity.item.model_dump_json()}\n"
                    f"Comps: {[comp.model_dump(mode='json') for comp in opportunity.comps[:3]]}\n"
                    f"Margin: {opportunity.margin.model_dump_json()}\n"
                    "Return only the typed review decision."
                ),
                deps=AgentServices(settings=self.settings),
            )
            decision = result.output
        except Exception:
            warnings.append(
                RunWarning(
                    code="llm_review_fallback",
                    message=(
                        f"Fell back to deterministic review for listing "
                        f"{opportunity.item.listing.listing_id} after LLM review failed."
                    ),
                )
            )
            return opportunity

        if not decision.approved:
            opportunity.rejection_reasons.extend(decision.rejection_reasons or ["review_rejected"])
        return opportunity

    def _normalized_item_from_extraction(
        self,
        listing: CollectedListing,
        extraction: ListingExtractionResult,
    ) -> NormalizedItem:
        return NormalizedItem(
            listing=listing,
            normalized_title=extraction.normalized_title,
            category=extraction.category,
            style_hint=extraction.style_hint,
            material_hint=extraction.material_hint,
            condition_summary=extraction.condition_summary,
            dimensions=extraction.dimensions,
            quality_flags=extraction.quality_flags,
            extraction_confidence=extraction.extraction_confidence,
        )

    def _build_plan(self, request: OpportunitySearchRequest) -> WorkflowPlan:
        if self.agent_pipeline:
            try:
                result = self.agent_pipeline.manager.run_sync(
                    (
                        "Build a search plan for this sourcing request.\n"
                        f"Query: {request.query}\n"
                        f"Max candidates: {request.max_candidates}\n"
                        "Return only the workflow plan."
                    ),
                    deps=AgentServices(settings=self.settings),
                )
                return result.output
            except Exception:
                pass
        category = "furniture and decor"
        notes = ["US market only.", "Rank by conservative margin."]
        return WorkflowPlan(
            rewritten_query=request.query.strip(),
            search_terms=[token.lower() for token in request.query.split() if token],
            category_focus=category,
            max_candidates=request.max_candidates,
            notes=notes,
        )


def build_orchestrator(settings: Settings | None = None) -> WorkflowOrchestrator:
    resolved_settings = settings or get_settings()
    agent_pipeline = None
    if resolved_settings.use_llm_agents and os.environ.get("OPENAI_API_KEY"):
        agent_pipeline = build_agent_pipeline(resolved_settings)
    if resolved_settings.live_mode_enabled:
        client = EbayBrowseClient(resolved_settings)
        return WorkflowOrchestrator(
            settings=resolved_settings,
            source_adapter=EbaySourceAdapter(client),
            resale_adapter=EbayResaleAdapter(client),
            agent_pipeline=agent_pipeline,
        )
    return WorkflowOrchestrator(
        settings=resolved_settings,
        source_adapter=DemoSourceAdapter(),
        resale_adapter=DemoResaleAdapter(),
        agent_pipeline=agent_pipeline,
    )
