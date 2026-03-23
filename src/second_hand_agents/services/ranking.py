from __future__ import annotations

from second_hand_agents.schemas import Opportunity


def dedupe_and_rank(
    opportunities: list[Opportunity],
) -> tuple[list[Opportunity], list[Opportunity]]:
    deduped: dict[str, Opportunity] = {}
    rejected: list[Opportunity] = []

    for opportunity in opportunities:
        if opportunity.rejection_reasons:
            rejected.append(opportunity)
            continue
        if not opportunity.margin:
            opportunity.rejection_reasons.append("missing_margin_estimate")
            rejected.append(opportunity)
            continue
        if opportunity.margin.estimated_profit <= 0:
            opportunity.rejection_reasons.append("non_positive_profit")
            rejected.append(opportunity)
            continue
        if opportunity.margin.confidence < 0.55:
            opportunity.rejection_reasons.append("low_confidence")
            rejected.append(opportunity)
            continue

        key = opportunity.item.normalized_title.lower()
        current = deduped.get(key)
        if (
            current is None
            or current.margin.estimated_margin_pct < opportunity.margin.estimated_margin_pct
        ):
            deduped[key] = opportunity

    accepted = sorted(
        deduped.values(),
        key=lambda opp: (
            opp.margin.estimated_margin_pct,
            opp.margin.estimated_profit,
            opp.margin.confidence,
        ),
        reverse=True,
    )
    for index, opportunity in enumerate(accepted, start=1):
        opportunity.rank = index
    return accepted, rejected
