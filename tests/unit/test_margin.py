from second_hand_agents.adapters.demo_data import SOURCE_LISTINGS
from second_hand_agents.config import Settings
from second_hand_agents.schemas import ComparableSale
from second_hand_agents.services.margin import estimate_margin
from second_hand_agents.services.normalization import normalize_listing


def test_estimate_margin_uses_conservative_discount() -> None:
    item = normalize_listing(SOURCE_LISTINGS[1])
    comps = [
        ComparableSale(
            marketplace="demo_resale",
            title="Lamp comp",
            url="https://example.com/comp-a",
            normalized_price=200,
            shipping_estimate=20,
            similarity_score=0.9,
        ),
        ComparableSale(
            marketplace="demo_resale",
            title="Lamp comp 2",
            url="https://example.com/comp-b",
            normalized_price=180,
            shipping_estimate=10,
            similarity_score=0.84,
        ),
    ]
    margin = estimate_margin(item, comps, Settings())

    assert margin is not None
    assert margin.conservative_comp_price < 200
    assert margin.estimated_profit > 0
    assert margin.estimated_margin_pct > 0
