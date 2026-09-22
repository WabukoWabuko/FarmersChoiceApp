from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal


@dataclass
class WorkerProfile:
    id: str
    name: str
    specialty: str
    location: str
    rating: float
    completed_jobs: int
    availability: str
    bio: str
    skills: list[str] = field(default_factory=list)
    comments: list[str] = field(default_factory=list)


@dataclass
class SponsorProfile:
    id: str
    name: str
    focus: str
    location: str
    funded_projects: int
    description: str
    verified: bool = True


@dataclass
class MarketplaceListing:
    id: str
    seller: str
    title: str
    category: str
    location: str
    price: float
    unit: str
    stock: str
    description: str
    seller_rating: float


@dataclass
class PlatformOrder:
    id: str
    listing_id: str
    buyer: str
    amount: float
    status: Literal["pending", "paid", "processing", "completed"]
    payment_method: str
    created_at: str


class PlatformService:
    """Local-first marketplace, workforce, sponsor, and payment domain service."""

    def __init__(self) -> None:
        self.workers = [
            WorkerProfile("worker-001", "Amina Wanjiku", "Irrigation & field care", "Nakuru", 4.9, 38, "Available this week", "Trusted field operator specializing in irrigation checks and crop maintenance.", ["Irrigation", "Crop scouting", "Record keeping"], ["Reliable and careful with our greenhouse.", "Completed the work ahead of schedule."]),
            WorkerProfile("worker-002", "David Otieno", "Land preparation", "Kisumu", 4.8, 24, "Available from 26 Sep", "Experienced in land preparation, planting support, and post-harvest handling.", ["Land preparation", "Planting", "Harvest support"], ["Strong team leader during planting season."]),
            WorkerProfile("worker-003", "Grace Chebet", "Pest scouting", "Uasin Gishu", 4.7, 19, "Available today", "Field scout who documents crop issues and escalates uncertain cases to agronomists.", ["Pest scouting", "Field reports", "Crop monitoring"], ["Her reports helped us act early."]),
        ]
        self.sponsors = [
            SponsorProfile("sponsor-001", "GreenGrow Cooperative", "Smallholder productivity", "Nakuru County", 17, "Supports farmer groups with inputs, training, and climate-smart practices."),
            SponsorProfile("sponsor-002", "HarvestBridge Foundation", "Youth agribusiness", "Kenya", 9, "Funds practical farm employment and market access for emerging growers."),
            SponsorProfile("sponsor-003", "AgriFuture Partners", "Water resilience", "East Africa", 23, "Backs irrigation, water harvesting, and resilient production projects."),
        ]
        self.listings = [
            MarketplaceListing("listing-001", "Mkulima Organics", "Composted dairy manure", "Manure & soil", "Nakuru", 1800, "per tonne", "12 tonnes", "Matured, screened manure suitable for field application.", 4.8),
            MarketplaceListing("listing-002", "Rift Seed Hub", "Certified maize seed", "Seeds", "Eldoret", 420, "per 2 kg", "85 packs", "Certified seed with batch information and delivery coordination.", 4.7),
            MarketplaceListing("listing-003", "WaterWise Supplies", "Drip irrigation starter kit", "Equipment", "Nairobi", 12500, "per kit", "16 kits", "Smallholder starter kit with filter, connectors, and field lines.", 4.9),
            MarketplaceListing("listing-004", "Lake Basin Produce", "Drying and storage bags", "Post-harvest", "Kisumu", 650, "per pack", "40 packs", "Reusable crop storage bags for safer post-harvest handling.", 4.6),
        ]
        self.orders: list[PlatformOrder] = []
        self.settings = {
            "alerts": True,
            "market_updates": True,
            "worker_messages": True,
            "offline_sync": True,
            "language": "English",
            "plan": "Farmer starter",
        }

    def create_order(self, listing: MarketplaceListing, buyer: str, payment_method: str) -> PlatformOrder:
        order = PlatformOrder(
            id=f"order-{len(self.orders) + 1:04d}",
            listing_id=listing.id,
            buyer=buyer,
            amount=listing.price,
            status="pending",
            payment_method=payment_method,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self.orders.append(order)
        return order

    def update_setting(self, key: str, value: object) -> None:
        if key in self.settings:
            self.settings[key] = value
