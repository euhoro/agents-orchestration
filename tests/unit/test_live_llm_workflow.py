from second_hand_agents.adapters.demo_data import RESALE_COMPS
from second_hand_agents.adapters.live_ebay import parse_listing
from second_hand_agents.config import Settings
from second_hand_agents.schemas import (
    ListingExtractionResult,
    OpportunitySearchRequest,
    ReviewDecision,
)
from second_hand_agents.services.workflow import WorkflowOrchestrator


class FakeRunResult:
    def __init__(self, output):
        self.output = output


class FakeAgent:
    def __init__(self, output=None, exc: Exception | None = None):
        self.output = output
        self.exc = exc

    def run_sync(self, *_args, **_kwargs):
        if self.exc:
            raise self.exc
        return FakeRunResult(self.output)


class FakeAgentPipeline:
    def __init__(
        self,
        extractor_output=None,
        extractor_exc: Exception | None = None,
        reviewer_output=None,
        reviewer_exc: Exception | None = None,
    ):
        self.manager = FakeAgent(exc=RuntimeError("unused"))
        self.extractor = FakeAgent(output=extractor_output, exc=extractor_exc)
        self.reviewer = FakeAgent(output=reviewer_output, exc=reviewer_exc)


class StaticSourceAdapter:
    def __init__(self, listing):
        self.listing = listing

    def search(self, _query: str, _max_candidates: int):
        return [self.listing]


class StaticResaleAdapter:
    def find_comps(self, _item):
        return RESALE_COMPS["lamp"]


def test_live_llm_extraction_and_review_approve() -> None:
    listing = build_listing()
    orchestrator = WorkflowOrchestrator(
        settings=Settings(mode="live"),
        source_adapter=StaticSourceAdapter(listing),
        resale_adapter=StaticResaleAdapter(),
        agent_pipeline=FakeAgentPipeline(
            extractor_output=ListingExtractionResult(
                normalized_title="Vintage teak table lamp",
                category="lighting",
                style_hint="vintage",
                material_hint="teak",
                condition_summary="Good second-hand condition.",
                dimensions=None,
                quality_flags=["visible_wear"],
                extraction_confidence=0.91,
                extraction_notes="clear lamp listing",
            ),
            reviewer_output=ReviewDecision(
                approved=True,
                rejection_reasons=[],
                review_confidence=0.88,
                review_notes="coherent candidate",
            ),
        ),
    )

    response = orchestrator.search(build_request())

    assert response.opportunities
    assert response.opportunities[0].item.normalized_title == "Vintage teak table lamp"
    assert not any(warning.code == "demo_mode" for warning in response.warnings)


def test_live_llm_extraction_failure_falls_back_with_warning() -> None:
    listing = build_listing()
    orchestrator = WorkflowOrchestrator(
        settings=Settings(mode="live"),
        source_adapter=StaticSourceAdapter(listing),
        resale_adapter=StaticResaleAdapter(),
        agent_pipeline=FakeAgentPipeline(
            extractor_exc=RuntimeError("boom"),
            reviewer_output=ReviewDecision(
                approved=True,
                rejection_reasons=[],
                review_confidence=0.8,
                review_notes="fallback extract okay",
            ),
        ),
    )

    response = orchestrator.search(build_request())

    assert response.opportunities
    assert any(warning.code == "llm_extraction_fallback" for warning in response.warnings)


def test_live_llm_review_rejection_moves_item_to_rejected() -> None:
    listing = build_listing()
    orchestrator = WorkflowOrchestrator(
        settings=Settings(mode="live"),
        source_adapter=StaticSourceAdapter(listing),
        resale_adapter=StaticResaleAdapter(),
        agent_pipeline=FakeAgentPipeline(
            extractor_output=ListingExtractionResult(
                normalized_title="Vintage teak table lamp",
                category="lighting",
                style_hint="vintage",
                material_hint="teak",
                condition_summary="Good second-hand condition.",
                dimensions=None,
                quality_flags=[],
                extraction_confidence=0.9,
                extraction_notes="clear lamp listing",
            ),
            reviewer_output=ReviewDecision(
                approved=False,
                rejection_reasons=["weak_comp_evidence"],
                review_confidence=0.76,
                review_notes="comps are too weak",
            ),
        ),
    )

    response = orchestrator.search(build_request())

    assert not response.opportunities
    assert response.rejected
    assert response.rejected[0].rejection_reasons == ["weak_comp_evidence"]


def test_live_llm_review_failure_falls_back_with_warning() -> None:
    listing = build_listing()
    orchestrator = WorkflowOrchestrator(
        settings=Settings(mode="live"),
        source_adapter=StaticSourceAdapter(listing),
        resale_adapter=StaticResaleAdapter(),
        agent_pipeline=FakeAgentPipeline(
            extractor_output=ListingExtractionResult(
                normalized_title="Vintage teak table lamp",
                category="lighting",
                style_hint="vintage",
                material_hint="teak",
                condition_summary="Good second-hand condition.",
                dimensions=None,
                quality_flags=[],
                extraction_confidence=0.9,
                extraction_notes="clear lamp listing",
            ),
            reviewer_exc=RuntimeError("boom"),
        ),
    )

    response = orchestrator.search(build_request())

    assert response.opportunities
    assert any(warning.code == "llm_review_fallback" for warning in response.warnings)


def build_request() -> OpportunitySearchRequest:
    return OpportunitySearchRequest(query="vintage lamp", top_k=3, max_candidates=3)


def build_listing():
    return parse_listing(
        {
            "itemId": "v1|123|0",
            "title": "Vintage teak lamp pre-owned",
            "price": {"value": "49.00"},
            "shippingOptions": [{"shippingCost": {"value": "12.00"}}],
            "condition": "Used",
            "itemWebUrl": "https://www.ebay.com/itm/123",
            "itemLocation": {"city": "Austin", "country": "US"},
            "shortDescription": "Teak body with linen shade and light surface wear.",
        },
        "ebay_live",
    )
