"""
Root Cause Engine — determines WHY revenue is at risk.

Supports two paths:
1. Mistral AI (structured reasoning) — when API key is available
2. Deterministic fallback (rule-based) — always available

The application never crashes because the AI API is unavailable.
"""

from __future__ import annotations

from app.config import settings


# ---------------------------------------------------------------------------
# Deterministic fallback rules
# ---------------------------------------------------------------------------
DECLINE_CODE_MAP: dict[str, tuple[str, float]] = {
    "05": ("insufficient_funds", 0.60),
    "51": ("insufficient_funds", 0.65),
    "06": ("temporary_bank_decline", 0.80),
    "91": ("temporary_bank_decline", 0.75),
    "54": ("expired_card", 0.90),
    "33": ("expired_card", 0.85),
    "14": ("invalid_payment_method", 0.70),
    "56": ("invalid_payment_method", 0.65),
    "mandate_fail": ("mandate_failure", 0.80),
    "auth_fail": ("authentication_failure", 0.75),
    "3ds_fail": ("authentication_failure", 0.70),
    "timeout": ("gateway_timeout", 0.80),
    "gateway_err": ("gateway_timeout", 0.75),
}

CHECKOUT_REASON_MAP: dict[str, tuple[str, float]] = {
    "session_timeout": ("session_timeout", 0.80),
    "payment_method_mismatch": ("payment_method_mismatch", 0.75),
    "user_inactivity": ("user_inactivity", 0.70),
    "payment_page_abandonment": ("payment_page_abandonment", 0.80),
    "price_sensitivity": ("price_sensitivity", 0.65),
    "technical_interruption": ("technical_interruption", 0.75),
}


def _diagnose_payment_deterministic(
    decline_code: str | None,
    failure_reason: str | None,
    customer_success_rate: float,
    customer_previous_payments: int,
) -> dict:
    """Rule-based diagnosis for payment failures."""
    # Try decline code first
    if decline_code and decline_code in DECLINE_CODE_MAP:
        root_cause, confidence = DECLINE_CODE_MAP[decline_code]
    elif failure_reason and failure_reason in DECLINE_CODE_MAP:
        root_cause, confidence = DECLINE_CODE_MAP[failure_reason]
    elif failure_reason:
        # Use the failure reason directly
        root_cause = failure_reason
        confidence = 0.55
    else:
        root_cause = "unknown_technical_failure"
        confidence = 0.40

    # Build evidence
    evidence = []
    if customer_previous_payments > 0:
        evidence.append(f"Customer has {customer_previous_payments} previous payment{'s' if customer_previous_payments > 1 else ''}")
    if customer_success_rate > 0.8:
        evidence.append("Strong payment history suggests temporary issue")
        confidence = min(0.95, confidence + 0.05)
    elif customer_success_rate < 0.5:
        evidence.append("History shows recurring payment difficulties")

    if root_cause == "temporary_bank_decline":
        evidence.append("Failure indicates temporary issuer issue")
    elif root_cause == "insufficient_funds":
        evidence.append("Decline code indicates insufficient account balance")
    elif root_cause == "expired_card":
        evidence.append("Payment method has expired or is no longer valid")

    if not evidence:
        evidence.append(f"Rule-based diagnosis: {root_cause} detected from failure code")

    return {
        "root_cause": root_cause,
        "confidence": round(confidence, 2),
        "evidence": evidence,
    }


def _diagnose_checkout_deterministic(
    abandonment_reason: str | None,
    page_reached: str | None,
) -> dict:
    """Rule-based diagnosis for checkout abandonment."""
    if abandonment_reason and abandonment_reason in CHECKOUT_REASON_MAP:
        root_cause, confidence = CHECKOUT_REASON_MAP[abandonment_reason]
    else:
        root_cause = "unknown_abandonment"
        confidence = 0.50

    evidence = []
    if page_reached:
        evidence.append(f"Customer reached {page_reached} page before abandoning")
    if root_cause == "price_sensitivity":
        evidence.append("Customer may have found pricing too high")
    elif root_cause == "session_timeout":
        evidence.append("Session expired before payment completion")
    elif root_cause == "technical_interruption":
        evidence.append("Technical issue prevented checkout completion")

    if not evidence:
        evidence.append(f"Rule-based diagnosis: {root_cause} detected from checkout data")

    return {
        "root_cause": root_cause,
        "confidence": round(confidence, 2),
        "evidence": evidence,
    }


def _diagnose_receivables_deterministic(
    days_overdue: int,
    dispute_flag: bool,
    customer_success_rate: float,
    hardship_flag: bool,
) -> dict:
    """Rule-based diagnosis for overdue receivables."""
    evidence = []

    if dispute_flag:
        root_cause = "dispute"
        confidence = 0.95
        evidence.append("Active dispute detected on this invoice")
    elif hardship_flag:
        root_cause = "cash_flow_issue"
        confidence = 0.80
        evidence.append("Customer flagged for financial hardship")
    elif days_overdue <= 7:
        root_cause = "first_time_late"
        confidence = 0.65
        evidence.append(f"Invoice is {days_overdue} days overdue — likely first-time delay")
        if customer_success_rate > 0.7:
            evidence.append("Customer has generally good payment history")
            confidence = 0.75
    elif days_overdue <= 30:
        root_cause = "administrative_delay"
        confidence = 0.60
        evidence.append(f"Invoice is {days_overdue} days overdue")
    elif days_overdue > 60:
        root_cause = "chronic_late_payer"
        confidence = 0.70
        evidence.append(f"Invoice is {days_overdue} days overdue — chronic pattern")
    else:
        root_cause = "first_time_late"
        confidence = 0.55
        evidence.append(f"Invoice is {days_overdue} days overdue")

    if not evidence:
        evidence.append(f"Rule-based diagnosis: {root_cause}")

    return {
        "root_cause": root_cause,
        "confidence": round(confidence, 2),
        "evidence": evidence,
    }


# ---------------------------------------------------------------------------
# Mistral-powered diagnosis
# ---------------------------------------------------------------------------
async def _diagnose_with_mistral(context: dict) -> dict | None:
    """
    Call Mistral for structured root-cause reasoning.
    Returns None on any failure — caller falls back to deterministic.
    """
    if not settings.mistral_available:
        return None

    try:
        from mistralai import Mistral

        client = Mistral(api_key=settings.MISTRAL_API_KEY)

        prompt = f"""You are a revenue recovery AI analyst. Analyze this failed transaction and provide a structured diagnosis.

Context:
- Recovery Type: {context.get('recovery_type')}
- Amount: ₹{context.get('amount')}
- Payment Method: {context.get('payment_method', 'N/A')}
- Failure Reason: {context.get('failure_reason', 'N/A')}
- Decline Code: {context.get('decline_code', 'N/A')}
- Customer Previous Payments: {context.get('previous_payments', 0)}
- Customer Previous Failures: {context.get('previous_failures', 0)}
- Customer LTV: ₹{context.get('ltv', 0)}
- Days Overdue: {context.get('days_overdue', 'N/A')}
- Dispute: {context.get('dispute', False)}
- Hardship: {context.get('hardship', False)}

Respond ONLY with valid JSON in this exact format:
{{
  "root_cause": "<one of: insufficient_funds, temporary_bank_decline, expired_card, invalid_payment_method, mandate_failure, authentication_failure, gateway_timeout, session_timeout, payment_method_mismatch, user_inactivity, payment_page_abandonment, price_sensitivity, technical_interruption, first_time_late, chronic_late_payer, dispute, administrative_delay, cash_flow_issue, unknown>",
  "confidence": <float 0-1>,
  "evidence": ["<evidence string 1>", "<evidence string 2>", "<evidence string 3>"]
}}"""

        response = await client.chat.complete_async(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=500,
        )

        import json
        content = response.choices[0].message.content.strip()
        # Strip markdown code fences if present
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            content = content.rsplit("```", 1)[0]
        result = json.loads(content)

        # Validate structure
        if "root_cause" in result and "confidence" in result and "evidence" in result:
            return result

    except Exception:
        pass  # Fall back to deterministic

    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
async def diagnose(
    recovery_type: str,
    decline_code: str | None = None,
    failure_reason: str | None = None,
    abandonment_reason: str | None = None,
    page_reached: str | None = None,
    days_overdue: int = 0,
    dispute_flag: bool = False,
    hardship_flag: bool = False,
    customer_success_rate: float = 0.5,
    customer_previous_payments: int = 0,
    amount: float = 0,
    payment_method: str | None = None,
    ltv: float = 0,
    previous_failures: int = 0,
) -> dict:
    """
    Diagnose root cause — tries Mistral first, falls back to deterministic.
    """
    # Try Mistral
    context = {
        "recovery_type": recovery_type,
        "amount": amount,
        "payment_method": payment_method,
        "failure_reason": failure_reason,
        "decline_code": decline_code,
        "previous_payments": customer_previous_payments,
        "previous_failures": previous_failures,
        "ltv": ltv,
        "days_overdue": days_overdue,
        "dispute": dispute_flag,
        "hardship": hardship_flag,
    }

    mistral_result = await _diagnose_with_mistral(context)
    if mistral_result:
        return mistral_result

    # Deterministic fallback
    if recovery_type == "PAYMENT":
        return _diagnose_payment_deterministic(
            decline_code, failure_reason, customer_success_rate, customer_previous_payments,
        )
    elif recovery_type == "CHECKOUT":
        return _diagnose_checkout_deterministic(abandonment_reason, page_reached)
    elif recovery_type == "RECEIVABLES":
        return _diagnose_receivables_deterministic(
            days_overdue, dispute_flag, customer_success_rate, hardship_flag,
        )

    return {
        "root_cause": "unknown",
        "confidence": 0.30,
        "evidence": ["Unable to determine root cause"],
    }
