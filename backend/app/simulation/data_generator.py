"""
RecoverAI — Synthetic Data Generator

Generates realistic Indian-market transaction data with behavioural diversity.
All values are computed — nothing is hardcoded as application state.
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import delete, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    Customer, Transaction, PaymentEvent, CheckoutEvent, Invoice,
    RecoveryCase, RecoveryAction, RecoveryLedger, PromiseToPay,
    BatchRun, AgentDecision, PolicyCheck, PolicyConfiguration,
    MandateSchedule,
)

# ---------------------------------------------------------------------------
# Name pools  (fictional Indian names / businesses)
# ---------------------------------------------------------------------------
FIRST_NAMES = [
    "Rahul", "Priya", "Arjun", "Sneha", "Vikram", "Ananya", "Rohan", "Kavita",
    "Amit", "Deepika", "Sanjay", "Meera", "Rajesh", "Pooja", "Nikhil", "Aarti",
    "Suresh", "Nisha", "Karan", "Divya", "Manish", "Ritu", "Arun", "Swati",
    "Gaurav", "Pallavi", "Vinay", "Shruti", "Manoj", "Neha", "Ashish", "Komal",
    "Pankaj", "Sapna", "Rakesh", "Anjali", "Vivek", "Preeti", "Sachin", "Sonali",
    "Dhruv", "Tanvi", "Harsh", "Isha", "Varun", "Megha", "Kunal", "Sonal",
    "Akash", "Jyoti", "Tarun", "Simran", "Mohit", "Rashi", "Vishal", "Aditi",
]

LAST_NAMES = [
    "Sharma", "Patel", "Gupta", "Singh", "Kumar", "Verma", "Joshi", "Mehta",
    "Shah", "Reddy", "Nair", "Iyer", "Desai", "Choudhary", "Malhotra", "Kapoor",
    "Agarwal", "Bhat", "Rao", "Pillai", "Saxena", "Khanna", "Bansal", "Jain",
    "Tiwari", "Mishra", "Pandey", "Dubey", "Srivastava", "Chauhan", "Thakur",
    "Bose", "Das", "Chatterjee", "Sen", "Roy", "Mukherjee", "Ghosh",
]

BUSINESS_NAMES = [
    "TechNova Solutions", "Zenith Enterprises", "CloudSphere India",
    "PixelCraft Studios", "GreenLeaf Organics", "SwiftPay Technologies",
    "DataBridge Analytics", "UrbanNest Interiors", "SkyLabs Innovations",
    "FreshBasket Foods", "CyberShield Security", "BlueOcean Logistics",
    "NexGen Software", "PrimeVista Consulting", "AquaPure Systems",
    "BrightStar Education", "MetaForge Industries", "HealthPlus Clinics",
    "EcoTrade Solutions", "DigiCraft Media", "Vortex Dynamics",
    "SilverLine Textiles", "GoldenGate Exports", "ClearView Optics",
    "PulsePoint Health", "RapidScale Cloud", "InfiniteLoop Tech",
    "CrystalPeak Mining", "HarvestMoon Agri", "QuantumEdge AI",
]

PAYMENT_METHODS = ["UPI", "credit_card", "debit_card", "net_banking", "mandate", "wallet"]

INDIAN_BANKS = [
    "HDFC Bank", "State Bank of India", "ICICI Bank", "Axis Bank",
    "Kotak Mahindra Bank", "Bank of Baroda", "Punjab National Bank"
]

MANDATE_TYPES = ["UPI_AUTOPAY", "E_NACH", "CARD_SI"]


def _generate_mandate_sequences(failure_reason: str, amount: float):
    now = datetime.now(timezone.utc)
    return [
        {
            "stage": 1,
            "title": "Stage 1: Soft Failure Cooldown & Re-presentation",
            "scheduled_time": (now - timedelta(hours=6)).isoformat(),
            "clearing_window": "Morning NACH Session (10:00 - 11:30 AM IST)",
            "liquidity_probability": 0.74,
            "channel": "eNACH Clearing Batch",
            "status": "COMPLETED",
            "result": "FAILED",
            "notes": f"Initial debit failed ({failure_reason}). 4h cooldown observed.",
        },
        {
            "stage": 2,
            "title": "Stage 2: High-Liquidity Morning Clearing Window",
            "scheduled_time": (now + timedelta(hours=3)).isoformat(),
            "clearing_window": "Morning NACH Session (10:00 - 11:30 AM IST)",
            "liquidity_probability": 0.86,
            "channel": "UPI AutoPay / eNACH Real-Time",
            "status": "IN_PROGRESS",
            "result": "PENDING",
            "notes": "Aligned with salary credit cycle and peak clearing liquidity window.",
        },
        {
            "stage": 3,
            "title": "Stage 3: RBI Pre-Debit Advisory & Fallback Retry",
            "scheduled_time": (now + timedelta(days=2)).isoformat(),
            "clearing_window": "Afternoon NACH Session (03:00 - 04:30 PM IST)",
            "liquidity_probability": 0.68,
            "channel": "Pre-Debit SMS + Mandate Re-presentation",
            "status": "SCHEDULED",
            "result": "PENDING",
            "notes": "Compliant 24h pre-debit advisory SMS sent before retry presentation.",
        },
        {
            "stage": 4,
            "title": "Stage 4: Dynamic Cascade / Payment Link Fallback",
            "scheduled_time": (now + timedelta(days=5)).isoformat(),
            "clearing_window": "Instant UPI Mandate Switch",
            "liquidity_probability": 0.55,
            "channel": "WhatsApp Interactive Link + Mandate Update",
            "status": "SCHEDULED",
            "result": "PENDING",
            "notes": "Offers one-click alternate payment method before marking mandate as revoked.",
        },
    ]

PAYMENT_FAILURE_REASONS = {
    "insufficient_funds": {"decline_codes": ["05", "51"], "weight": 15},
    "temporary_bank_decline": {"decline_codes": ["06", "91"], "weight": 10},
    "expired_card": {"decline_codes": ["54", "33"], "weight": 8},
    "invalid_payment_method": {"decline_codes": ["14", "56"], "weight": 3},
    "mandate_failure": {"decline_codes": ["mandate_fail"], "weight": 2},
    "authentication_failure": {"decline_codes": ["auth_fail", "3ds_fail"], "weight": 3},
    "gateway_timeout": {"decline_codes": ["timeout", "gateway_err"], "weight": 4},
}

PAYMENT_EVENT_TYPES = [
    "failed_payment", "failed_subscription_renewal", "upi_failure",
    "card_decline", "mandate_failure", "authentication_failure", "gateway_timeout",
]

CHECKOUT_ABANDONMENT_REASONS = [
    "session_timeout", "payment_method_mismatch", "user_inactivity",
    "payment_page_abandonment", "price_sensitivity", "technical_interruption",
]

CHECKOUT_PAGES = ["cart", "checkout", "payment_page", "otp", "confirmation"]

AMOUNT_TIERS = [
    (499, 1499, 30),     # low value
    (1500, 4999, 25),    # mid-low
    (5000, 18000, 25),   # mid
    (18001, 50000, 12),  # mid-high
    (50001, 120000, 5),  # high
    (120001, 850000, 3), # very high
]


def _pick_amount(avg: float = 5000) -> Decimal:
    """Pick a realistic INR amount weighted by tier."""
    tier = random.choices(AMOUNT_TIERS, weights=[t[2] for t in AMOUNT_TIERS], k=1)[0]
    raw = random.randint(tier[0], tier[1])
    # Round to neat values
    if raw < 1000:
        raw = round(raw / 100) * 100 - 1  # e.g. 499, 599
    elif raw < 10000:
        raw = round(raw / 500) * 500 - 1  # e.g. 2499, 4999
    else:
        raw = round(raw / 1000) * 1000
    return Decimal(max(raw, 99))


def _random_name() -> tuple[str, str]:
    return random.choice(FIRST_NAMES), random.choice(LAST_NAMES)


def _random_email(first: str, last: str) -> str:
    domains = ["gmail.com", "yahoo.co.in", "outlook.com", "hotmail.com", "company.in"]
    return f"{first.lower()}.{last.lower()}{random.randint(1,99)}@{random.choice(domains)}"


def _random_phone() -> str:
    return f"+91{random.randint(7000000000, 9999999999)}"


# ---------------------------------------------------------------------------
# Customer generator
# ---------------------------------------------------------------------------
def generate_customers(count: int) -> list[dict]:
    customers = []
    for _ in range(count):
        first, last = _random_name()
        ltv_tier = random.choices(
            ["high", "mid", "low"],
            weights=[20, 50, 30], k=1
        )[0]
        if ltv_tier == "high":
            ltv = Decimal(random.randint(50000, 500000))
            tenure = random.randint(12, 60)
            prev_payments = random.randint(20, 100)
        elif ltv_tier == "mid":
            ltv = Decimal(random.randint(10000, 49999))
            tenure = random.randint(3, 24)
            prev_payments = random.randint(5, 30)
        else:
            ltv = Decimal(random.randint(1000, 9999))
            tenure = random.randint(1, 6)
            prev_payments = random.randint(0, 8)

        prev_failures = random.randint(0, max(1, prev_payments // 4))
        has_dispute = random.random() < 0.15
        has_opt_out = random.random() < 0.10
        has_hardship = random.random() < 0.05

        customers.append({
            "name": f"{first} {last}",
            "email": _random_email(first, last),
            "phone": _random_phone(),
            "business_name": random.choice(BUSINESS_NAMES) if random.random() < 0.3 else None,
            "ltv": ltv,
            "tenure_months": tenure,
            "previous_payments": prev_payments,
            "previous_failures": prev_failures,
            "consent_status": True,
            "opt_out": has_opt_out,
            "dispute_status": has_dispute,
            "hardship_status": has_hardship,
        })
    return customers


# ---------------------------------------------------------------------------
# Event generators
# ---------------------------------------------------------------------------
def generate_payment_events(customer_ids: list[int], count: int) -> list[dict]:
    events = []
    failure_pool = []
    for reason, info in PAYMENT_FAILURE_REASONS.items():
        failure_pool.extend([(reason, info["decline_codes"])] * info["weight"])

    for _ in range(count):
        reason, codes = random.choice(failure_pool)
        events.append({
            "customer_id": random.choice(customer_ids),
            "amount": _pick_amount(),
            "payment_method": random.choice(PAYMENT_METHODS),
            "failure_reason": reason,
            "decline_code": random.choice(codes),
            "status": "FAILED",
            "event_type": random.choice(PAYMENT_EVENT_TYPES),
            "created_at": datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 72)),
        })
    return events


def generate_checkout_events(customer_ids: list[int], count: int) -> list[dict]:
    events = []
    for _ in range(count):
        events.append({
            "customer_id": random.choice(customer_ids),
            "amount": _pick_amount(),
            "session_id": str(uuid.uuid4())[:12],
            "payment_method": random.choice(PAYMENT_METHODS),
            "abandonment_reason": random.choice(CHECKOUT_ABANDONMENT_REASONS),
            "page_reached": random.choice(CHECKOUT_PAGES),
            "status": "ABANDONED",
            "created_at": datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 48)),
        })
    return events


def generate_invoices(customer_ids: list[int], count: int) -> list[dict]:
    invoices = []
    for i in range(count):
        days_overdue = random.choice([
            *[random.randint(1, 7)] * 10,     # first-time late
            *[random.randint(30, 60)] * 10,    # chronic
            *[random.randint(8, 29)] * 5,      # moderate
            *[random.randint(61, 120)] * 5,    # severe
        ])
        has_dispute = random.random() < 0.17
        invoices.append({
            "customer_id": random.choice(customer_ids),
            "invoice_number": f"INV-{2024_0000 + i + 1}",
            "amount": _pick_amount(),
            "issue_date": datetime.now(timezone.utc) - timedelta(days=days_overdue + 30),
            "due_date": datetime.now(timezone.utc) - timedelta(days=days_overdue),
            "days_overdue": days_overdue,
            "dispute_flag": has_dispute,
            "status": "DISPUTED" if has_dispute else "OVERDUE",
        })
    return invoices


# ---------------------------------------------------------------------------
# Full dataset generator
# ---------------------------------------------------------------------------
async def generate_dataset(
    db: AsyncSession,
    batch_size: int = 100,
    payment_pct: float = 40,
    checkout_pct: float = 30,
    receivables_pct: float = 30,
    avg_transaction_value: float = 5000,
    failure_rate: float = 0.6,
) -> dict:
    """Generate a complete synthetic dataset and persist it."""
    payment_count = int(batch_size * payment_pct / 100)
    checkout_count = int(batch_size * checkout_pct / 100)
    receivables_count = batch_size - payment_count - checkout_count

    # Generate unique customers (roughly 60-70% of batch size for variety)
    num_customers = max(10, int(batch_size * 0.65))
    customer_dicts = generate_customers(num_customers)

    # Persist customers
    customer_objs = []
    for c in customer_dicts:
        obj = Customer(**c)
        db.add(obj)
        customer_objs.append(obj)
    await db.flush()
    customer_ids = [c.id for c in customer_objs]

    # Generate & persist payment events + recovery cases
    payment_events_data = generate_payment_events(customer_ids, payment_count)
    payment_cases = 0
    for pe in payment_events_data:
        pe_obj = PaymentEvent(**pe)
        db.add(pe_obj)
        await db.flush()
        # Also create a transaction record
        txn = Transaction(
            customer_id=pe["customer_id"],
            amount=pe["amount"],
            payment_method=pe["payment_method"],
            status="FAILED",
            failure_reason=pe["failure_reason"],
        )
        db.add(txn)
        await db.flush()
        pe_obj.transaction_id = txn.id

        # Create recovery case
        rc = RecoveryCase(
            payment_event_id=pe_obj.id,
            customer_id=pe["customer_id"],
            amount_at_risk=pe["amount"],
            recovery_type="PAYMENT",
            status="PENDING",
        )
        db.add(rc)
        await db.flush()

        # Seed mandate schedule for recurring/mandate events and first set of payment cases
        if payment_cases < 10 or pe.get("payment_method") == "mandate" or "mandate" in pe.get("failure_reason", ""):
            bank = random.choice(INDIAN_BANKS)
            mtype = random.choice(MANDATE_TYPES)
            amt = float(pe["amount"])
            mandate_obj = MandateSchedule(
                customer_id=pe["customer_id"],
                case_id=rc.id,
                umrn=f"UMRN/{bank[:4].upper()}/{2026}/{10000 + payment_cases}",
                mandate_type=mtype,
                bank_name=bank,
                amount=Decimal(str(amt)),
                max_amount=Decimal(str(round(amt * 2.5, 2))),
                frequency="MONTHLY",
                status="RESEQUENCED",
                current_stage=2,
                failure_reason=pe["failure_reason"],
                decline_code=pe.get("decline_code") or "mandate_fail",
                pre_debit_notified=True,
                sequences=_generate_mandate_sequences(pe["failure_reason"], amt),
                next_presentation_at=datetime.now(timezone.utc) + timedelta(hours=3),
            )
            db.add(mandate_obj)

        payment_cases += 1

    # Generate & persist checkout events + recovery cases
    checkout_events_data = generate_checkout_events(customer_ids, checkout_count)
    checkout_cases = 0
    for ce in checkout_events_data:
        ce_obj = CheckoutEvent(**ce)
        db.add(ce_obj)
        await db.flush()
        rc = RecoveryCase(
            checkout_event_id=ce_obj.id,
            customer_id=ce["customer_id"],
            amount_at_risk=ce["amount"],
            recovery_type="CHECKOUT",
            status="PENDING",
        )
        db.add(rc)
        checkout_cases += 1

    # Generate & persist invoices + recovery cases
    invoices_data = generate_invoices(customer_ids, receivables_count)
    invoice_cases = 0
    for inv in invoices_data:
        inv_obj = Invoice(**inv)
        db.add(inv_obj)
        await db.flush()
        rc = RecoveryCase(
            invoice_id=inv_obj.id,
            customer_id=inv["customer_id"],
            amount_at_risk=inv["amount"],
            recovery_type="RECEIVABLES",
            status="PENDING",
        )
        db.add(rc)
        invoice_cases += 1

    await db.flush()

    return {
        "customers_created": len(customer_objs),
        "payment_events": payment_cases,
        "checkout_events": checkout_cases,
        "invoices": invoice_cases,
        "recovery_cases": payment_cases + checkout_cases + invoice_cases,
    }


# ---------------------------------------------------------------------------
# Seed initial data  (run once on first startup)
# ---------------------------------------------------------------------------
async def seed_initial_data(db: AsyncSession) -> None:
    """Seed 100 cases on first run."""
    # Check if data already exists
    from sqlalchemy import func, select
    result = await db.execute(select(func.count(Customer.id)))
    count = result.scalar()
    if count and count > 0:
        # Check if mandates exist; if not, backfill for existing cases
        mandate_count_res = await db.execute(select(func.count(MandateSchedule.id)))
        if (mandate_count_res.scalar() or 0) == 0:
            await _seed_mandates_for_existing_cases(db)
        return  # already seeded

    await generate_dataset(db, batch_size=100, payment_pct=40, checkout_pct=30, receivables_pct=30)
    await _seed_default_policies(db)
    await db.commit()


async def _seed_mandates_for_existing_cases(db: AsyncSession) -> None:
    """Backfill mandates for existing payment cases."""
    from sqlalchemy import select
    cases_res = await db.execute(select(RecoveryCase).where(RecoveryCase.recovery_type == "PAYMENT").limit(15))
    cases = cases_res.scalars().all()
    now = datetime.now(timezone.utc)
    for idx, c in enumerate(cases):
        bank = random.choice(INDIAN_BANKS)
        mtype = random.choice(MANDATE_TYPES)
        amt = float(c.amount_at_risk)
        mandate_obj = MandateSchedule(
            customer_id=c.customer_id,
            case_id=c.id,
            umrn=f"UMRN/{bank[:4].upper()}/{2026}/{10000 + idx + 1}",
            mandate_type=mtype,
            bank_name=bank,
            amount=Decimal(str(amt)),
            max_amount=Decimal(str(round(amt * 2.5, 2))),
            frequency="MONTHLY",
            status="RESEQUENCED" if idx % 4 != 0 else "RECOVERED",
            current_stage=2 if idx % 4 != 0 else 1,
            failure_reason="mandate_fail",
            decline_code="mandate_fail",
            pre_debit_notified=True,
            sequences=_generate_mandate_sequences("mandate_fail", amt),
            next_presentation_at=now + timedelta(hours=idx * 2 + 1) if idx % 4 != 0 else None,
        )
        db.add(mandate_obj)
    await db.commit()


async def _seed_default_policies(db: AsyncSession) -> None:
    """Insert default policy configuration values."""
    from sqlalchemy import select
    result = await db.execute(select(PolicyConfiguration).limit(1))
    if result.scalar():
        return

    defaults = [
        ("MAX_PAYMENT_RETRIES", "3", "Maximum number of automated payment retries per case"),
        ("RETRY_COOLDOWN_HOURS", "4", "Minimum hours between retry attempts"),
        ("MAX_CONTACTS_PER_DAY", "3", "Maximum customer contacts per day across all channels"),
        ("HIGH_VALUE_THRESHOLD", "50000", "Amount (INR) above which human approval is required"),
        ("MAX_DUNNING_DAYS", "90", "Maximum days to pursue receivables recovery"),
        ("MIN_EXPECTED_VALUE", "0", "Minimum expected recovery value to proceed with action"),
    ]
    for key, value, desc in defaults:
        db.add(PolicyConfiguration(key=key, value=value, description=desc))


# ---------------------------------------------------------------------------
# Reset demo
# ---------------------------------------------------------------------------
async def reset_demo(db: AsyncSession) -> None:
    """Clear all demo data and re-seed."""
    # Delete in dependency order
    for model in [
        PolicyCheck, AgentDecision, RecoveryLedger, RecoveryAction,
        MandateSchedule, PromiseToPay, RecoveryCase, PaymentEvent, CheckoutEvent,
        Invoice, Transaction, Customer, BatchRun, PolicyConfiguration,
    ]:
        await db.execute(delete(model))
    await db.flush()

    await generate_dataset(db, batch_size=100, payment_pct=40, checkout_pct=30, receivables_pct=30)
    await _seed_default_policies(db)
    await db.commit()
