import httpx

from second_hand_agents.adapters.live_ebay import (
    EbayAuthClient,
    EbayBrowseClient,
    EbayResaleAdapter,
    EbaySourceAdapter,
)
from second_hand_agents.config import Settings
from second_hand_agents.services.normalization import normalize_listing


def test_live_source_adapter_parses_second_hand_listings() -> None:
    client = build_mock_browse_client()
    adapter = EbaySourceAdapter(client)

    listings = adapter.search("vintage lamp", 5)

    assert listings
    assert listings[0].source_marketplace == "ebay_live"
    assert listings[0].asking_price == 89.0


def test_live_resale_adapter_returns_similarity_scored_comps() -> None:
    client = build_mock_browse_client()
    source = EbaySourceAdapter(client)
    item = normalize_listing(source.search("vintage lamp", 1)[0])
    adapter = EbayResaleAdapter(client)

    comps = adapter.find_comps(item)

    assert comps
    assert comps[0].marketplace == "ebay_live_comps"
    assert all(comp.similarity_score >= 0.35 for comp in comps)


def build_mock_browse_client() -> EbayBrowseClient:
    settings = Settings(
        mode="live",
        ebay_client_id="test-id",
        ebay_client_secret="test-secret",
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/identity/v1/oauth2/token"):
            return httpx.Response(
                200,
                json={"access_token": "token", "expires_in": 7200},
            )

        return httpx.Response(
            200,
            json={
                "itemSummaries": [
                    {
                        "itemId": "v1|123|0",
                        "title": "Vintage teak lamp pre-owned",
                        "price": {"value": "89.00"},
                        "shippingOptions": [{"shippingCost": {"value": "15.00"}}],
                        "condition": "Used",
                        "itemWebUrl": "https://www.ebay.com/itm/123",
                        "itemLocation": {"city": "Austin", "country": "US"},
                    },
                    {
                        "itemId": "v1|456|0",
                        "title": "Teak bedside lamp used",
                        "price": {"value": "139.00"},
                        "shippingOptions": [{"shippingCost": {"value": "18.00"}}],
                        "condition": "Pre-Owned",
                        "itemWebUrl": "https://www.ebay.com/itm/456",
                        "itemLocation": {"city": "Dallas", "country": "US"},
                    },
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    auth = EbayAuthClient(settings, http_client)
    return EbayBrowseClient(settings, auth_client=auth, client=http_client)
