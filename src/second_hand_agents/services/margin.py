from __future__ import annotations

from statistics import median

from second_hand_agents.config import Settings
from second_hand_agents.schemas import ComparableSale, MarginEstimate, NormalizedItem


def estimate_margin(
    item: NormalizedItem,
    comps: list[ComparableSale],
    settings: Settings,
) -> MarginEstimate | None:
    usable = [comp for comp in comps if comp.similarity_score >= 0.75]
    if not usable:
        return None

    total_values = sorted(comp.total_value for comp in usable)
    baseline = total_values[0] if len(total_values) == 1 else median(total_values[:2])
    conservative_comp_price = round(baseline * settings.safety_discount, 2)
    acquisition_cost = round(item.listing.asking_price + item.listing.shipping_price, 2)
    outbound_shipping = estimate_outbound_shipping(item)
    resale_fees = round(conservative_comp_price * settings.resale_fee_rate, 2)
    estimated_profit = round(
        conservative_comp_price - resale_fees - outbound_shipping - acquisition_cost,
        2,
    )
    estimated_margin_pct = round(
        (estimated_profit / acquisition_cost) if acquisition_cost else 0.0,
        4,
    )
    confidence = round(
        min(0.97, 0.62 + (sum(comp.similarity_score for comp in usable[:3]) / len(usable[:3])) / 3),
        2,
    )
    if "missing_dimensions" in item.quality_flags:
        confidence = round(max(0.4, confidence - 0.1), 2)
    return MarginEstimate(
        expected_resale_price=conservative_comp_price,
        conservative_comp_price=conservative_comp_price,
        resale_fees=resale_fees,
        outbound_shipping=outbound_shipping,
        acquisition_cost=acquisition_cost,
        estimated_profit=estimated_profit,
        estimated_margin_pct=estimated_margin_pct,
        confidence=confidence,
        rationale=(
            "Conservative estimate based on discounted comparable sales, resale fees, "
            "and category-specific outbound shipping."
        ),
    )


def estimate_outbound_shipping(item: NormalizedItem) -> float:
    if item.category == "lighting":
        return 18.0
    if item.category == "decor":
        return 16.0
    return 38.0
