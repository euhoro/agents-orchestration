from __future__ import annotations

import re

from second_hand_agents.schemas import CollectedListing, NormalizedItem

STYLE_KEYWORDS = {
    "mid-century": "mid-century",
    "vintage": "vintage",
    "arched": "arched",
    "pedestal": "pedestal",
}

MATERIAL_KEYWORDS = {
    "wood": "wood",
    "walnut": "walnut",
    "teak": "teak",
    "brass": "brass",
    "ceramic": "ceramic",
    "cane": "cane",
}


def normalize_listing(listing: CollectedListing) -> NormalizedItem:
    text = f"{listing.title} {listing.raw_content}".lower()
    category = infer_category(text)
    style_hint = first_match(text, STYLE_KEYWORDS)
    material_hint = first_match(text, MATERIAL_KEYWORDS)
    dimensions = extract_dimensions(listing.raw_content)
    quality_flags = []
    if "minor wear" in text or "faint patina" in text or "finish marks" in text:
        quality_flags.append("visible_wear")
    if "rewiring" in text:
        quality_flags.append("updated_electrics")
    if dimensions is None and category in {"furniture", "lighting"}:
        quality_flags.append("missing_dimensions")
    confidence = 0.88
    if "missing_dimensions" in quality_flags:
        confidence -= 0.08
    return NormalizedItem(
        listing=listing,
        normalized_title=clean_title(listing.title),
        category=category,
        style_hint=style_hint,
        material_hint=material_hint,
        condition_summary=summarize_condition(text),
        dimensions=dimensions,
        quality_flags=quality_flags,
        extraction_confidence=round(max(0.55, confidence), 2),
    )


def infer_category(text: str) -> str:
    if any(token in text for token in {"chair", "table", "stool"}):
        return "furniture"
    if "lamp" in text:
        return "lighting"
    if "mirror" in text:
        return "decor"
    return "mixed"


def clean_title(title: str) -> str:
    return re.sub(r"\s+", " ", title).strip()


def summarize_condition(text: str) -> str:
    if "minor wear" in text or "finish marks" in text or "patina" in text:
        return "Good vintage condition with visible wear."
    if "works as shown" in text or "clean rewiring" in text:
        return "Good functional condition."
    return "Good second-hand condition."


def extract_dimensions(text: str) -> str | None:
    match = re.search(r"\d+\s?(?:x|by)\s?\d+(?:\s?(?:x|by)\s?\d+)?", text.lower())
    return match.group(0) if match else None


def first_match(text: str, mapping: dict[str, str]) -> str | None:
    for token, value in mapping.items():
        if token in text:
            return value
    return None
