from __future__ import annotations

from second_hand_agents.schemas import CollectedListing, ComparableSale

SOURCE_LISTINGS: list[CollectedListing] = [
    CollectedListing(
        source_marketplace="demo_curated",
        listing_id="chair-01",
        title="Vintage cane accent chair by Drexel",
        url="https://example.com/listings/chair-01",
        asking_price=165,
        shipping_price=35,
        location="Brooklyn, NY",
        raw_content=(
            "Warm walnut frame, intact cane seat, minor wear on arms, designer-looking "
            "silhouette, photographed in daylight."
        ),
        image_hint="single cane chair",
    ),
    CollectedListing(
        source_marketplace="demo_curated",
        listing_id="lamp-01",
        title="Mid-century teak table lamp with linen shade",
        url="https://example.com/listings/lamp-01",
        asking_price=62,
        shipping_price=14,
        location="Austin, TX",
        raw_content=(
            "Vintage teak lamp, clean rewiring, soft wear at base, neutral linen shade, "
            "works as shown."
        ),
        image_hint="teak lamp",
    ),
    CollectedListing(
        source_marketplace="demo_curated",
        listing_id="mirror-01",
        title="Arched brass wall mirror",
        url="https://example.com/listings/mirror-01",
        asking_price=70,
        shipping_price=18,
        location="Portland, OR",
        raw_content=(
            "Decor mirror with brass finish, faint patina, no cracks, apartment-friendly "
            "scale, curated boutique styling."
        ),
        image_hint="arched brass mirror",
    ),
    CollectedListing(
        source_marketplace="demo_curated",
        listing_id="table-01",
        title="Solid wood pedestal side table",
        url="https://example.com/listings/table-01",
        asking_price=118,
        shipping_price=24,
        location="Chicago, IL",
        raw_content=(
            "Chunky round pedestal side table in stained wood, small finish marks, "
            "designer-inspired shape, sturdy and heavy."
        ),
        image_hint="pedestal side table",
    ),
    CollectedListing(
        source_marketplace="demo_curated",
        listing_id="stool-01",
        title="Vintage ceramic garden stool in emerald glaze",
        url="https://example.com/listings/stool-01",
        asking_price=85,
        shipping_price=20,
        location="Los Angeles, CA",
        raw_content=(
            "High gloss ceramic stool, bright emerald glaze, one tiny flea bite at the base, "
            "indoor or patio use."
        ),
        image_hint="ceramic garden stool",
    ),
]


RESALE_COMPS: dict[str, list[ComparableSale]] = {
    "chair": [
        ComparableSale(
            marketplace="demo_resale",
            title="Drexel cane accent chair",
            url="https://example.com/comps/chair-1",
            normalized_price=345,
            shipping_estimate=48,
            similarity_score=0.91,
        ),
        ComparableSale(
            marketplace="demo_resale",
            title="Walnut cane side chair",
            url="https://example.com/comps/chair-2",
            normalized_price=298,
            shipping_estimate=45,
            similarity_score=0.86,
        ),
        ComparableSale(
            marketplace="demo_resale",
            title="Vintage cane lounge chair",
            url="https://example.com/comps/chair-3",
            normalized_price=315,
            shipping_estimate=55,
            similarity_score=0.84,
        ),
    ],
    "lamp": [
        ComparableSale(
            marketplace="demo_resale",
            title="Teak table lamp with linen shade",
            url="https://example.com/comps/lamp-1",
            normalized_price=185,
            shipping_estimate=18,
            similarity_score=0.92,
        ),
        ComparableSale(
            marketplace="demo_resale",
            title="Mid-century wood lamp",
            url="https://example.com/comps/lamp-2",
            normalized_price=168,
            shipping_estimate=16,
            similarity_score=0.83,
        ),
        ComparableSale(
            marketplace="demo_resale",
            title="Vintage teak bedside lamp",
            url="https://example.com/comps/lamp-3",
            normalized_price=176,
            shipping_estimate=14,
            similarity_score=0.81,
        ),
    ],
    "mirror": [
        ComparableSale(
            marketplace="demo_resale",
            title="Arched brass mirror",
            url="https://example.com/comps/mirror-1",
            normalized_price=154,
            shipping_estimate=20,
            similarity_score=0.9,
        ),
        ComparableSale(
            marketplace="demo_resale",
            title="Vintage brass wall mirror",
            url="https://example.com/comps/mirror-2",
            normalized_price=142,
            shipping_estimate=22,
            similarity_score=0.79,
        ),
    ],
    "table": [
        ComparableSale(
            marketplace="demo_resale",
            title="Pedestal wood side table",
            url="https://example.com/comps/table-1",
            normalized_price=265,
            shipping_estimate=35,
            similarity_score=0.88,
        ),
        ComparableSale(
            marketplace="demo_resale",
            title="Round stained wood side table",
            url="https://example.com/comps/table-2",
            normalized_price=238,
            shipping_estimate=28,
            similarity_score=0.81,
        ),
    ],
    "stool": [
        ComparableSale(
            marketplace="demo_resale",
            title="Emerald ceramic garden stool",
            url="https://example.com/comps/stool-1",
            normalized_price=190,
            shipping_estimate=24,
            similarity_score=0.87,
        ),
        ComparableSale(
            marketplace="demo_resale",
            title="Green ceramic accent stool",
            url="https://example.com/comps/stool-2",
            normalized_price=176,
            shipping_estimate=26,
            similarity_score=0.78,
        ),
    ],
}
