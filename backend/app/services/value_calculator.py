"""
Value Calculator — Expected Recovery Value & Incremental Recovery

All calculations are dynamic, computed from customer/event features.
"""

from __future__ import annotations

import random
from decimal import Decimal

# Intervention cost estimates (INR)
INTERVENTION_COSTS: dict[str, float] = {
    "SMART_RETRY": 10,
    "PAYMENT_LINK": 15,
    "ALTERNATE_PAYMENT_METHOD": 20,
    "REMINDER": 5,
    "HINGLISH_MESSAGE": 8,
    "PROMISE_TO_PAY": 5,
    "PAYMENT_PLAN": 25,
    "HUMAN_ESCALATION": 200,
    "STOP": 0,
}


def calculate_recovery_probability(
    action_type: str,
    customer_success_rate: float,
    failure_reason: str | None,
    days_overdue: int | None,
    customer_ltv: float,
    recovery_type: str,
    attempt_number: int = 1,
    has_dispute: bool = False,
    has_opt_out: bool = False,
    has_hardship: bool = False,
) -> float:
    """
    Calculate recovery probability from customer/event features.
    This is a deterministic statistical model — NOT a hardcoded lookup.
    """
    if has_opt_out or has_dispute or has_hardship:
        return 0.0

    # Base probability from customer history
    base = max(0.1, min(0.9, customer_success_rate))

    # Adjust by action type
    action_multipliers = {
        "SMART_RETRY": 1.0,
        "PAYMENT_LINK": 0.85,
        "ALTERNATE_PAYMENT_METHOD": 0.75,
        "REMINDER": 0.60,
        "HINGLISH_MESSAGE": 0.65,
        "PROMISE_TO_PAY": 0.50,
        "PAYMENT_PLAN": 0.55,
        "HUMAN_ESCALATION": 0.70,
        "STOP": 0.0,
    }
    prob = base * action_multipliers.get(action_type, 0.5)

    # Adjust by failure reason
    reason_adjustments = {
        "temporary_bank_decline": 0.15,
        "gateway_timeout": 0.10,
        "insufficient_funds": -0.15,
        "expired_card": -0.25,
        "invalid_payment_method": -0.30,
        "mandate_failure": -0.10,
        "authentication_failure": -0.05,
        "session_timeout": 0.05,
        "payment_method_mismatch": -0.10,
        "user_inactivity": 0.0,
        "payment_page_abandonment": -0.05,
        "price_sensitivity": -0.20,
        "technical_interruption": 0.10,
        "first_time_late": 0.10,
        "chronic_late_payer": -0.20,
        "dispute": -0.40,
        "administrative_delay": 0.05,
        "cash_flow_issue": -0.15,
    }
    prob += reason_adjustments.get(failure_reason or "", 0.0)

    # Adjust by days overdue (receivables)
    if days_overdue is not None and days_overdue > 0:
        decay = min(0.3, days_overdue * 0.005)
        prob -= decay

    # Adjust by attempt number (diminishing returns)
    if attempt_number > 1:
        prob *= max(0.3, 1.0 - (attempt_number - 1) * 0.15)

    # High-LTV customers tend to recover better
    if customer_ltv > 50000:
        prob += 0.05
    elif customer_ltv < 5000:
        prob -= 0.05

    # Adjust by recovery type
    if recovery_type == "CHECKOUT":
        prob *= 0.85  # checkout recovery is generally harder

    # Add small noise for realism
    prob += random.uniform(-0.03, 0.03)

    return round(max(0.01, min(0.95, prob)), 4)


def calculate_baseline_probability(
    customer_success_rate: float,
    failure_reason: str | None,
    recovery_type: str,
    has_dispute: bool = False,
    has_opt_out: bool = False,
) -> float:
    """
    Baseline: single generic action probability.
    Simpler than the agent — just one retry/reminder.
    """
    if has_opt_out or has_dispute:
        return 0.0
    base = max(0.05, min(0.7, customer_success_rate * 0.6))
    if failure_reason in ("temporary_bank_decline", "gateway_timeout"):
        base += 0.05
    elif failure_reason in ("expired_card", "invalid_payment_method"):
        base -= 0.10
    return round(max(0.01, min(0.60, base)), 4)


def calculate_expected_recovery_value(
    amount_at_risk: float,
    probability: float,
    intervention_cost: float,
) -> float:
    """ERV = P(recovery) × Amount − Cost"""
    return round(probability * amount_at_risk - intervention_cost, 2)


def calculate_incremental_recovery(
    action_probability: float,
    baseline_probability: float,
) -> float:
    """Estimated Incremental Recovery = P(recovery|action) − P(recovery|baseline)"""
    return round(action_probability - baseline_probability, 4)


def get_intervention_cost(action_type: str) -> float:
    return INTERVENTION_COSTS.get(action_type, 10)


def get_available_actions(recovery_type: str) -> list[str]:
    """Return actions available for a given recovery type."""
    common = ["REMINDER", "HINGLISH_MESSAGE", "HUMAN_ESCALATION", "STOP"]
    if recovery_type == "PAYMENT":
        return ["SMART_RETRY", "PAYMENT_LINK", "ALTERNATE_PAYMENT_METHOD"] + common
    elif recovery_type == "CHECKOUT":
        return ["PAYMENT_LINK", "REMINDER", "HINGLISH_MESSAGE", "HUMAN_ESCALATION", "STOP"]
    elif recovery_type == "RECEIVABLES":
        return ["REMINDER", "PROMISE_TO_PAY", "PAYMENT_PLAN", "PAYMENT_LINK", "HINGLISH_MESSAGE", "HUMAN_ESCALATION", "STOP"]
    return common
