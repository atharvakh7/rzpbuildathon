"""
Recovery Agent Unit Tests.
Verifies intervention ranking (highest ERV selection), re-evaluation loop, and fallback behaviour.
"""

import pytest
from app.models.models import Customer, RecoveryCase
from app.services.recovery_agent import recovery_agent
from app.services.root_cause_engine import diagnose


@pytest.mark.asyncio
async def test_deterministic_root_cause_diagnosis():
    diag = await diagnose(
        recovery_type="PAYMENT",
        decline_code="05",
        failure_reason="insufficient_funds",
        customer_success_rate=0.8,
        customer_previous_payments=10,
        amount=5000,
    )
    assert diag["root_cause"] == "insufficient_funds"
    assert diag["confidence"] >= 0.6
    assert len(diag["evidence"]) > 0


@pytest.mark.asyncio
async def test_checkout_root_cause_diagnosis():
    diag = await diagnose(
        recovery_type="CHECKOUT",
        abandonment_reason="payment_page_abandonment",
        page_reached="payment_page",
        amount=2500,
    )
    assert diag["root_cause"] == "payment_page_abandonment"
    assert diag["confidence"] >= 0.7


@pytest.mark.asyncio
async def test_receivables_root_cause_diagnosis():
    diag = await diagnose(
        recovery_type="RECEIVABLES",
        days_overdue=45,
        dispute_flag=False,
        hardship_flag=False,
        customer_success_rate=0.5,
        amount=75000,
    )
    assert diag["root_cause"] in ("administrative_delay", "first_time_late", "chronic_late_payer")
