from second_hand_agents.adapters.demo_data import RESALE_COMPS, SOURCE_LISTINGS
from second_hand_agents.config import Settings
from second_hand_agents.schemas import Opportunity
from second_hand_agents.services.margin import estimate_margin
from second_hand_agents.services.normalization import normalize_listing
from second_hand_agents.services.ranking import dedupe_and_rank


def build_opportunity(index: int, comp_key: str) -> Opportunity:
    item = normalize_listing(SOURCE_LISTINGS[index])
    margin = estimate_margin(item, RESALE_COMPS[comp_key], Settings())
    return Opportunity(item=item, comps=RESALE_COMPS[comp_key], margin=margin)


def test_dedupe_and_rank_orders_by_margin_then_profit() -> None:
    chair = build_opportunity(0, "chair")
    lamp = build_opportunity(1, "lamp")
    table = build_opportunity(3, "table")

    accepted, rejected = dedupe_and_rank([lamp, chair, table])

    assert not rejected
    assert accepted[0].margin.estimated_margin_pct >= accepted[1].margin.estimated_margin_pct
    assert accepted[0].rank == 1
