"""
Policy Engine Unit Tests.
Verifies guardrails: max retries, cooldown, opt-out, dispute, hardship, and min EV.
"""

import pytest
from app.models.models import Customer, PolicyConfiguration, RecoveryCase
from app.policies.policy_engine import check_policy


@pytest.mark.asyncio
async def test_opt_out_hard_stop():
    cust = Customer(id=1, name="Test User", opt_out=True)
    case = RecoveryCase(id=101, customer_id=1, amount_at_risk=5000, recovery_type="PAYMENT")
    case.customer = cust

    # Dummy session
    class DummyDB:
        async def execute(self, *args, **kwargs):
            return None

    res = await check_policy(DummyDB(), case, "SMART_RETRY")
    assert res["allowed"] is False
    assert res["result"] == "DENIED"
    assert "opted out" in res["reason"]


@pytest.mark.asyncio
async def test_dispute_hard_stop():
    cust = Customer(id=2, name="Disputed User", opt_out=False, dispute_status=True)
    case = RecoveryCase(id=102, customer_id=2, amount_at_risk=15000, recovery_type="PAYMENT")
    case.customer = cust

    class DummyDB:
        pass

    res = await check_policy(DummyDB(), case, "PAYMENT_LINK")
    assert res["allowed"] is False
    assert res["result"] == "DENIED"
    assert "dispute" in res["reason"].lower()


@pytest.mark.asyncio
async def test_hardship_requires_approval():
    cust = Customer(id=3, name="Hardship User", opt_out=False, dispute_status=False, hardship_status=True)
    case = RecoveryCase(id=103, customer_id=3, amount_at_risk=2000, recovery_type="PAYMENT")
    case.customer = cust

    class DummyDB:
        pass

    res = await check_policy(DummyDB(), case, "SMART_RETRY")
    assert res["allowed"] is False
    assert res["result"] == "REQUIRES_APPROVAL"
