from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from second_hand_agents.adapters.demo_data import RESALE_COMPS, SOURCE_LISTINGS
from second_hand_agents.schemas import CollectedListing, ComparableSale, NormalizedItem


class BaseSourceAdapter(Protocol):
    name: str

    def search(self, query: str, max_candidates: int) -> list[CollectedListing]: ...


class BaseResaleAdapter(Protocol):
    name: str

    def find_comps(self, item: NormalizedItem) -> list[ComparableSale]: ...


class DemoSourceAdapter:
    name = "demo_curated"

    def __init__(self, listings: Iterable[CollectedListing] | None = None) -> None:
        self._listings = list(listings or SOURCE_LISTINGS)

    def search(self, query: str, max_candidates: int) -> list[CollectedListing]:
        terms = {term.lower() for term in query.split()}
        ranked = sorted(
            self._listings,
            key=lambda listing: sum(token in listing.title.lower() for token in terms),
            reverse=True,
        )
        filtered = [item for item in ranked if any(term in item.title.lower() for term in terms)]
        return (filtered or ranked)[:max_candidates]


class DemoResaleAdapter:
    name = "demo_resale"

    def find_comps(self, item: NormalizedItem) -> list[ComparableSale]:
        title = item.normalized_title.lower()
        if "chair" in title:
            key = "chair"
        elif "lamp" in title:
            key = "lamp"
        elif "mirror" in title:
            key = "mirror"
        elif "table" in title:
            key = "table"
        else:
            key = "stool"
        return list(RESALE_COMPS.get(key, []))
