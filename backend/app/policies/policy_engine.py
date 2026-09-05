"""
Policy Engine — deterministic guardrails for recovery actions.

The LLM can recommend, but the policy engine decides whether the action is allowed.
Policy values are read from the database at check time — changing a policy
in the UI changes actual agent behavior.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    PolicyConfiguration, RecoveryCase, RecoveryAction, Customer, PolicyCheck,
)


async def _get_policy_value(db: AsyncSession, key: str, default: str) -> str:
    """Read a policy value from the database."""
    result = await db.execute(
        select(PolicyConfiguration.value).where(PolicyConfiguration.key == key)
    )
    value = result.scalar()
    return value if value is not None else default


async def check_policy(
    db: AsyncSession,
    case: RecoveryCase,
    action_type: str,
    expected_recovery_value: float = 0,
) -> dict:
    """
    Check whether an action is allowed by the policy engine.
    Returns {"allowed": bool, "result": str, "reason": str}
    result is one of: ALLOWED, DENIED, REQUIRES_APPROVAL
    """
    customer = case.customer
    if customer is None:
        result = await db.execute(select(Customer).where(Customer.id == case.customer_id))
        customer = result.scalar_one_or_none()

    # ----- HARD STOP CONDITIONS -----

    # 1. Customer opt-out — NEVER allowed
    if customer and customer.opt_out:
        return _deny("Customer has opted out of communications. No actions permitted.")

    # 2. Dispute detected — NEVER allowed
    if customer and customer.dispute_status:
        return _deny("Active dispute detected. All automated actions blocked.")

    # 3. Hardship flag — requires human
    if customer and customer.hardship_status:
        if action_type != "HUMAN_ESCALATION":
            return _requires_approval("Customer flagged for financial hardship. Human review required.")

    # 4. Already recovered
    if case.status == "RECOVERED":
        return _deny("Case already recovered. No further action needed.")

    # 5. STOP action is always allowed
    if action_type == "STOP":
        return _allow("STOP action is always permitted.")

    # ----- CONFIGURABLE POLICY CHECKS -----

    # 6. Maximum retries
    max_retries = int(await _get_policy_value(db, "MAX_PAYMENT_RETRIES", "3"))
    if action_type == "SMART_RETRY":
        retry_count = await _count_actions(db, case.id, "SMART_RETRY")
        if retry_count >= max_retries:
            return _deny(f"Maximum payment retries ({max_retries}) reached. {retry_count}/{max_retries} used.")

    # 7. Retry cooldown
    cooldown_hours = int(await _get_policy_value(db, "RETRY_COOLDOWN_HOURS", "4"))
    if action_type == "SMART_RETRY":
        last_retry = await _last_action_time(db, case.id, "SMART_RETRY")
        if last_retry:
            cooldown_end = last_retry + timedelta(hours=cooldown_hours)
            if datetime.now(timezone.utc) < cooldown_end.replace(tzinfo=timezone.utc) if cooldown_end.tzinfo is None else cooldown_end:
                return _deny(f"Retry cooldown ({cooldown_hours}h) not yet elapsed. Last retry at {last_retry.isoformat()}.")

    # 8. Maximum contacts per day
    max_contacts = int(await _get_policy_value(db, "MAX_CONTACTS_PER_DAY", "3"))
    contact_actions = ["REMINDER", "HINGLISH_MESSAGE", "PAYMENT_LINK"]
    if action_type in contact_actions:
        today_contacts = await _count_today_actions(db, case.customer_id, contact_actions)
        if today_contacts >= max_contacts:
            return _deny(f"Maximum daily contacts ({max_contacts}) reached. {today_contacts}/{max_contacts} used today.")

    # 9. High-value threshold — requires approval
    high_value = float(await _get_policy_value(db, "HIGH_VALUE_THRESHOLD", "50000"))
    if float(case.amount_at_risk) >= high_value:
        if action_type not in ("HUMAN_ESCALATION", "STOP"):
            return _requires_approval(
                f"High-value case (₹{float(case.amount_at_risk):,.0f} ≥ ₹{high_value:,.0f}). Human approval required."
            )

    # 10. Maximum dunning days (receivables)
    if case.recovery_type == "RECEIVABLES":
        max_dunning = int(await _get_policy_value(db, "MAX_DUNNING_DAYS", "90"))
        if case.invoice and hasattr(case.invoice, "days_overdue") and case.invoice.days_overdue:
            if case.invoice.days_overdue > max_dunning:
                return _deny(f"Maximum dunning period ({max_dunning} days) exceeded. Invoice is {case.invoice.days_overdue} days overdue.")

    # 11. Negative expected value
    min_ev = float(await _get_policy_value(db, "MIN_EXPECTED_VALUE", "0"))
    if expected_recovery_value < min_ev:
        return _deny(f"Expected recovery value (₹{expected_recovery_value:,.0f}) below minimum threshold (₹{min_ev:,.0f}).")

    # 12. Maximum total attempts
    total_attempts = case.attempt_count or 0
    if total_attempts >= 10:
        return _deny(f"Maximum total attempts (10) reached. Case has {total_attempts} attempts.")

    return _allow("All policy checks passed.")


async def _count_actions(db: AsyncSession, case_id: int, action_type: str) -> int:
    result = await db.execute(
        select(func.count(RecoveryAction.id)).where(
            RecoveryAction.case_id == case_id,
            RecoveryAction.action_type == action_type,
        )
    )
    return result.scalar() or 0


async def _last_action_time(db: AsyncSession, case_id: int, action_type: str) -> datetime | None:
    result = await db.execute(
        select(RecoveryAction.created_at).where(
            RecoveryAction.case_id == case_id,
            RecoveryAction.action_type == action_type,
        ).order_by(RecoveryAction.created_at.desc()).limit(1)
    )
    return result.scalar()


async def _count_today_actions(db: AsyncSession, customer_id: int, action_types: list[str]) -> int:
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    result = await db.execute(
        select(func.count(RecoveryAction.id)).join(RecoveryCase).where(
            RecoveryCase.customer_id == customer_id,
            RecoveryAction.action_type.in_(action_types),
            RecoveryAction.created_at >= today_start,
        )
    )
    return result.scalar() or 0


def _allow(reason: str) -> dict:
    return {"allowed": True, "result": "ALLOWED", "reason": reason}


def _deny(reason: str) -> dict:
    return {"allowed": False, "result": "DENIED", "reason": reason}


def _requires_approval(reason: str) -> dict:
    return {"allowed": False, "result": "REQUIRES_APPROVAL", "reason": reason}


async def log_policy_check(
    db: AsyncSession,
    case_id: int,
    action_type: str,
    result: str,
    reason: str,
) -> None:
    """Record a policy check in the audit log."""
    check = PolicyCheck(
        case_id=case_id,
        action_type=action_type,
        result=result,
        reason=reason,
    )
    db.add(check)
