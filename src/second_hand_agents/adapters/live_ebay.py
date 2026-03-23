from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from second_hand_agents.config import Settings
from second_hand_agents.schemas import CollectedListing, ComparableSale, NormalizedItem

USED_CONDITIONS = {"used", "pre-owned", "seller refurbished", "open box"}


@dataclass
class EbayAccessToken:
    value: str
    expires_at: datetime

    def is_valid(self) -> bool:
        return datetime.now(UTC) < self.expires_at


class EbayAuthClient:
    def __init__(self, settings: Settings, client: httpx.Client | None = None) -> None:
        self.settings = settings
        self.client = client or httpx.Client(timeout=settings.request_timeout_seconds)
        self._token: EbayAccessToken | None = None

    def get_access_token(self) -> str:
        if self._token and self._token.is_valid():
            return self._token.value

        if not self.settings.ebay_client_id or not self.settings.ebay_client_secret:
            raise ValueError("Missing eBay credentials for live mode.")

        credentials = (
            f"{self.settings.ebay_client_id}:{self.settings.ebay_client_secret}".encode()
        )
        auth_header = base64.b64encode(credentials).decode("ascii")
        response = self.client.post(
            f"{self.settings.ebay_base_url}/identity/v1/oauth2/token",
            headers={
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "client_credentials",
                "scope": self.settings.ebay_scope,
            },
        )
        response.raise_for_status()
        payload = response.json()
        expires_in = int(payload.get("expires_in", 7200))
        self._token = EbayAccessToken(
            value=payload["access_token"],
            expires_at=datetime.now(UTC) + timedelta(seconds=max(60, expires_in - 60)),
        )
        return self._token.value


class EbayBrowseClient:
    def __init__(
        self,
        settings: Settings,
        auth_client: EbayAuthClient | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.settings = settings
        self.client = client or httpx.Client(timeout=settings.request_timeout_seconds)
        self.auth_client = auth_client or EbayAuthClient(settings, self.client)

    def search_items(self, query: str, limit: int) -> list[dict[str, Any]]:
        token = self.auth_client.get_access_token()
        response = self.client.get(
            f"{self.settings.ebay_base_url}/buy/browse/v1/item_summary/search",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            params={
                "q": query,
                "limit": limit,
            },
        )
        response.raise_for_status()
        data = response.json()
        return data.get("itemSummaries", [])


class EbaySourceAdapter:
    name = "ebay_live"

    def __init__(self, client: EbayBrowseClient) -> None:
        self.client = client

    def search(self, query: str, max_candidates: int) -> list[CollectedListing]:
        items = self.client.search_items(query, max_candidates * 2)
        listings = [parse_listing(item, self.name) for item in items]
        filtered = [listing for listing in listings if is_second_hand(listing.raw_content)]
        return filtered[:max_candidates]


class EbayResaleAdapter:
    name = "ebay_live_comps"

    def __init__(self, client: EbayBrowseClient) -> None:
        self.client = client

    def find_comps(self, item: NormalizedItem) -> list[ComparableSale]:
        items = self.client.search_items(item.normalized_title, 8)
        comps = [parse_comp(summary, item.normalized_title, self.name) for summary in items]
        return [comp for comp in comps if comp.similarity_score >= 0.35][:5]


def parse_listing(item: dict[str, Any], marketplace: str) -> CollectedListing:
    title = item.get("title", "Unknown listing")
    price = parse_money(item.get("price"))
    shipping = parse_shipping(item.get("shippingOptions", []))
    location = parse_location(item)
    raw_content_parts = [
        title,
        item.get("condition", ""),
        item.get("shortDescription", ""),
        item.get("itemGroupType", ""),
    ]
    return CollectedListing(
        source_marketplace=marketplace,
        listing_id=item.get("itemId", title.lower().replace(" ", "-")),
        title=title,
        url=item.get("itemWebUrl", "https://www.ebay.com"),
        asking_price=price,
        shipping_price=shipping,
        location=location,
        raw_content=" | ".join(part for part in raw_content_parts if part),
        image_hint=item.get("image", {}).get("imageUrl"),
    )


def parse_comp(item: dict[str, Any], reference_title: str, marketplace: str) -> ComparableSale:
    title = item.get("title", "Unknown comp")
    shipping = parse_shipping(item.get("shippingOptions", []))
    price = parse_money(item.get("price"))
    return ComparableSale(
        marketplace=marketplace,
        title=title,
        url=item.get("itemWebUrl", "https://www.ebay.com"),
        sold=False,
        normalized_price=price,
        shipping_estimate=shipping,
        similarity_score=title_similarity(reference_title, title),
    )


def parse_money(value: dict[str, Any] | None) -> float:
    if not value:
        return 0.0
    return round(float(value.get("value", 0.0)), 2)


def parse_shipping(options: list[dict[str, Any]]) -> float:
    if not options:
        return 0.0
    first = options[0]
    return parse_money(first.get("shippingCost"))


def parse_location(item: dict[str, Any]) -> str:
    item_location = item.get("itemLocation") or {}
    city = item_location.get("city")
    country = item_location.get("country")
    if city and country:
        return f"{city}, {country}"
    return city or country or "Unknown"


def is_second_hand(raw_content: str) -> bool:
    lowered = raw_content.lower()
    return any(condition in lowered for condition in USED_CONDITIONS)


def title_similarity(reference: str, candidate: str) -> float:
    left = set(reference.lower().split())
    right = set(candidate.lower().split())
    if not left or not right:
        return 0.0
    overlap = len(left & right)
    return round(overlap / max(len(left), len(right)), 2)
