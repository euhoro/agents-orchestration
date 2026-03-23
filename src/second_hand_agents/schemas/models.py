from __future__ import annotations

from datetime import UTC, datetime
from statistics import mean
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, HttpUrl, computed_field


class OpportunitySearchRequest(BaseModel):
    query: str = Field(min_length=2)
    region: Literal["US"] = "US"
    max_candidates: int = Field(default=12, ge=1, le=50)
    top_k: int = Field(default=10, ge=1, le=25)
    source_marketplaces: list[str] = Field(default_factory=list)
    resale_marketplaces: list[str] = Field(default_factory=list)


class WorkflowPlan(BaseModel):
    rewritten_query: str
    search_terms: list[str]
    category_focus: str
    max_candidates: int
    notes: list[str] = Field(default_factory=list)


class CollectedListing(BaseModel):
    source_marketplace: str
    listing_id: str
    title: str
    url: HttpUrl
    asking_price: float = Field(ge=0)
    shipping_price: float = Field(default=0, ge=0)
    location: str
    collected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    raw_content: str
    image_hint: str | None = None

    @computed_field
    @property
    def total_purchase_cost(self) -> float:
        return round(self.asking_price + self.shipping_price, 2)


class NormalizedItem(BaseModel):
    listing: CollectedListing
    normalized_title: str
    category: Literal["furniture", "decor", "lighting", "mixed"]
    style_hint: str | None = None
    material_hint: str | None = None
    condition_summary: str
    dimensions: str | None = None
    quality_flags: list[str] = Field(default_factory=list)
    extraction_confidence: float = Field(ge=0, le=1)


class ListingExtractionResult(BaseModel):
    normalized_title: str
    category: Literal["furniture", "decor", "lighting", "mixed"]
    style_hint: str | None = None
    material_hint: str | None = None
    condition_summary: str
    dimensions: str | None = None
    quality_flags: list[str] = Field(default_factory=list)
    extraction_confidence: float = Field(ge=0, le=1)
    extraction_notes: str = ""


class ComparableSale(BaseModel):
    marketplace: str
    title: str
    url: HttpUrl
    sold: bool = True
    sold_at: datetime | None = None
    normalized_price: float = Field(ge=0)
    shipping_estimate: float = Field(default=0, ge=0)
    similarity_score: float = Field(ge=0, le=1)

    @computed_field
    @property
    def total_value(self) -> float:
        return round(self.normalized_price + self.shipping_estimate, 2)


class MarginEstimate(BaseModel):
    expected_resale_price: float = Field(ge=0)
    conservative_comp_price: float = Field(ge=0)
    resale_fees: float = Field(ge=0)
    outbound_shipping: float = Field(ge=0)
    acquisition_cost: float = Field(ge=0)
    estimated_profit: float
    estimated_margin_pct: float
    confidence: float = Field(ge=0, le=1)
    rationale: str


class Opportunity(BaseModel):
    rank: int | None = None
    item: NormalizedItem
    comps: list[ComparableSale]
    margin: MarginEstimate | None = None
    rejection_reasons: list[str] = Field(default_factory=list)

    @computed_field
    @property
    def accepted(self) -> bool:
        return self.margin is not None and not self.rejection_reasons


class ReviewDecision(BaseModel):
    approved: bool
    rejection_reasons: list[str] = Field(default_factory=list)
    review_confidence: float = Field(ge=0, le=1)
    review_notes: str = ""


class RunWarning(BaseModel):
    code: str
    message: str


class OpportunitySearchResponse(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    request: OpportunitySearchRequest
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    opportunities: list[Opportunity]
    rejected: list[Opportunity] = Field(default_factory=list)
    warnings: list[RunWarning] = Field(default_factory=list)

    @computed_field
    @property
    def average_margin_pct(self) -> float:
        accepted = [item.margin.estimated_margin_pct for item in self.opportunities if item.margin]
        return round(mean(accepted), 4) if accepted else 0.0
