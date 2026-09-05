"""
Value Calculator Unit Tests.
Verifies dynamic ERV and incremental recovery calculations.
"""

from app.services.value_calculator import (
    calculate_baseline_probability,
    calculate_expected_recovery_value,
    calculate_incremental_recovery,
    calculate_recovery_probability,
    get_available_actions,
    get_intervention_cost,
)


def test_expected_recovery_value_formula():
    amount = 10000.0
    probability = 0.72
    cost = 10.0
    # ERV = 10000 * 0.72 - 10 = 7200 - 10 = 7190
    erv = calculate_expected_recovery_value(amount, probability, cost)
    assert erv == 7190.0


def test_incremental_recovery_formula():
    action_prob = 0.75
    baseline_prob = 0.40
    incr = calculate_incremental_recovery(action_prob, baseline_prob)
    assert round(incr, 2) == 0.35


def test_zero_recovery_for_opt_out_or_dispute():
    prob_opt_out = calculate_recovery_probability(
        action_type="SMART_RETRY",
        customer_success_rate=0.9,
        failure_reason="temporary_bank_decline",
        days_overdue=0,
        customer_ltv=100000,
        recovery_type="PAYMENT",
        has_opt_out=True,
    )
    assert prob_opt_out == 0.0

    prob_dispute = calculate_recovery_probability(
        action_type="SMART_RETRY",
        customer_success_rate=0.9,
        failure_reason="temporary_bank_decline",
        days_overdue=0,
        customer_ltv=100000,
        recovery_type="PAYMENT",
        has_dispute=True,
    )
    assert prob_dispute == 0.0


def test_available_actions_by_category():
    payment_actions = get_available_actions("PAYMENT")
    assert "SMART_RETRY" in payment_actions
    assert "PAYMENT_LINK" in payment_actions

    checkout_actions = get_available_actions("CHECKOUT")
    assert "SMART_RETRY" not in checkout_actions
    assert "PAYMENT_LINK" in checkout_actions

    receivables_actions = get_available_actions("RECEIVABLES")
    assert "PROMISE_TO_PAY" in receivables_actions
    assert "PAYMENT_PLAN" in receivables_actions
