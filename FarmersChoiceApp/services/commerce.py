from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass
class WorkerProfile:
    id: str
    name: str
    trade: str
    location: str
    bio: str
    rating: float
    completed_jobs: int
    verified: bool = True
    skills: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    comments: list[str] = field(default_factory=list)


@dataclass
class Sponsor:
    id: str
    name: str
    focus: str
    location: str
    description: str
    verified: bool = True


@dataclass
class MarketplaceListing:
    id: str
    title: str
    category: str
    seller: str
    location: str
    price: float
    unit: str
    stock: int
    description: str
    verified: bool = True


@dataclass
class BuyerRequest:
    id: str
    buyer: str
    product: str
    quantity: str
    location: str
    status: str = "Open"


@dataclass
class Payment:
    id: str
    amount: float
    currency: str
    recipient: str
    method: str
    status: str
    created_at: str
    reference: str


@dataclass
class JobPost:
    id: str
    farmer: str
    title: str
    location: str
    budget: str
    schedule: str
    status: str = "Open"
    applicants: list[str] = field(default_factory=list)


@dataclass
class Order:
    id: str
    buyer: str
    listing_id: str
    product: str
    quantity: int
    total: float
    status: str = "Awaiting payment"
    escrow_status: str = "Not funded"
    delivery_status: str = "Not dispatched"
    dispute_status: str = "None"


@dataclass
class Notification:
    id: str
    title: str
    message: str
    category: str
    read: bool = False


@dataclass
class AuditLog:
    id: str
    actor: str
    action: str
    target: str
    created_at: str


class CommerceService:
    """Local-first commerce, workforce, sponsorship, and payment domain service."""

    def __init__(self) -> None:
        self.workers = [
            WorkerProfile("w-001", "Mary Wanjiku", "Irrigation specialist", "Nakuru", "Efficient drip and pump installations for smallholder farms.", 4.9, 48, skills=["Drip irrigation", "Pump repair", "Water audits"], recommendations=["Reliable and punctual on every visit."], comments=["Saved our tomato crop during a dry spell."]),
            WorkerProfile("w-002", "Peter Otieno", "Farm labour team lead", "Kisumu", "Coordinates trusted teams for planting, weeding, and harvest work.", 4.7, 63, skills=["Planting", "Harvest coordination", "Post-harvest handling"], recommendations=["Organized a team of ten workers with no delays."], comments=["Good communication and fair pricing."]),
            WorkerProfile("w-003", "Amina Hassan", "Agronomy field scout", "Mombasa", "Field scouting, pest observations, and crop monitoring support.", 4.8, 31, skills=["Crop scouting", "Pest monitoring", "Field records"], recommendations=["Her reports are clear and actionable."], comments=["Spotted disease early and helped us contain it."]),
        ]
        self.sponsors = [
            Sponsor("s-001", "GreenFuture Cooperative", "Climate-smart farming", "Nakuru", "Supports water-efficient farming, training, and resilient seed access."),
            Sponsor("s-002", "Harvest Growth Fund", "Smallholder finance", "Kenya", "Connects verified farms with seasonal input and equipment financing."),
            Sponsor("s-003", "AgriWomen Network", "Women-led farms", "Kisumu", "Provides mentorship, market access, and farm-business support."),
        ]
        self.listings = [
            MarketplaceListing("l-001", "Composted dairy manure", "Organic inputs", "Nakuru Soil Works", "Nakuru", 1800, "tonne", 24, "Screened and composted manure for soil improvement."),
            MarketplaceListing("l-002", "Certified maize seed", "Seed", "Rift Seed House", "Eldoret", 420, "2 kg pack", 90, "Season-ready certified seed with batch traceability."),
            MarketplaceListing("l-003", "Solar irrigation pump", "Equipment", "SunFlow Agri", "Nairobi", 68500, "unit", 6, "Off-grid pump package with installation support."),
        ]
        self.requests: list[BuyerRequest] = []
        self.payments: list[Payment] = []
        self.jobs: list[JobPost] = []
        self.orders: list[Order] = []
        self.notifications: list[Notification] = [
            Notification("n-001", "Welcome to Farmers' Choice", "Complete your farm location to unlock automatic analysis.", "Onboarding"),
            Notification("n-002", "New sponsor program", "GreenFuture Cooperative has opened a climate-smart farming program.", "Opportunity"),
        ]
        self.audit_logs: list[AuditLog] = []

    def search_workers(self, query: str = "") -> list[WorkerProfile]:
        query = query.strip().lower()
        if not query:
            return self.workers
        return [worker for worker in self.workers if query in f"{worker.name} {worker.trade} {worker.location} {' '.join(worker.skills)}".lower()]

    def search_listings(self, query: str = "") -> list[MarketplaceListing]:
        query = query.strip().lower()
        if not query:
            return self.listings
        return [listing for listing in self.listings if query in f"{listing.title} {listing.category} {listing.seller} {listing.location}".lower()]

    def create_buyer_request(self, buyer: str, product: str, quantity: str, location: str) -> BuyerRequest:
        request = BuyerRequest(str(uuid4()), buyer, product, quantity, location)
        self.requests.insert(0, request)
        return request

    def create_payment(self, amount: float, recipient: str, method: str) -> Payment:
        if amount <= 0:
            raise ValueError("Payment amount must be greater than zero.")
        reference = f"FC-{datetime.now(timezone.utc):%Y%m%d}-{uuid4().hex[:6].upper()}"
        payment = Payment(str(uuid4()), amount, "KES", recipient, method, "Pending confirmation", datetime.now(timezone.utc).isoformat(), reference)
        self.payments.insert(0, payment)
        return payment

    def create_job(self, farmer: str, title: str, location: str, budget: str, schedule: str) -> JobPost:
        job = JobPost(str(uuid4()), farmer, title, location, budget, schedule)
        self.jobs.insert(0, job)
        self.notifications.insert(0, Notification(str(uuid4()), "Job posted", f"{title} is now visible to available laborers.", "Workforce"))
        return job

    def apply_for_job(self, job: JobPost, worker_name: str) -> None:
        if worker_name not in job.applicants:
            job.applicants.append(worker_name)
            self.notifications.insert(0, Notification(str(uuid4()), "New job application", f"{worker_name} applied for {job.title}.", "Workforce"))

    def create_order(self, buyer: str, listing: MarketplaceListing, quantity: int) -> Order:
        if quantity <= 0 or quantity > listing.stock:
            raise ValueError("Quantity is not available.")
        listing.stock -= quantity
        order = Order(str(uuid4()), buyer, listing.id, listing.title, quantity, listing.price * quantity)
        self.orders.insert(0, order)
        self.notifications.insert(0, Notification(str(uuid4()), "Order created", f"Your order for {listing.title} is ready for secure checkout.", "Marketplace"))
        return order

    def fund_escrow(self, order: Order) -> None:
        order.escrow_status = "Funded"
        order.status = "Payment secured"
        self.audit_logs.insert(0, AuditLog(str(uuid4()), order.buyer, "funded_escrow", order.id, datetime.now(timezone.utc).isoformat()))

    def report_order(self, order: Order) -> None:
        order.dispute_status = "Under review"
        self.notifications.insert(0, Notification(str(uuid4()), "Dispute opened", f"Order {order.id[:8]} is under review.", "Trust & safety"))

    def unread_notifications(self) -> list[Notification]:
        return [notification for notification in self.notifications if not notification.read]

    def qr_payload(self, item_type: str, item_id: str, label: str) -> str:
        return f"farmerschoice://{item_type}/{item_id}?label={label.replace(' ', '%20')}"


__all__ = ["AuditLog", "BuyerRequest", "CommerceService", "JobPost", "MarketplaceListing", "Notification", "Order", "Payment", "Sponsor", "WorkerProfile"]
