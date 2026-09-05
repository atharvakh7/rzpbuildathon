"""
RecoverAI — SQLAlchemy ORM Models

13 tables with proper foreign keys and relationships.
The database is the single source of truth for all business state.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, Numeric, Boolean, DateTime,
    ForeignKey, Text, JSON,
)
from sqlalchemy.orm import relationship

from app.database.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Customer
# ---------------------------------------------------------------------------
class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200))
    phone = Column(String(20))
    business_name = Column(String(300))
    ltv = Column(Numeric(12, 2), default=0)
    tenure_months = Column(Integer, default=0)
    previous_payments = Column(Integer, default=0)
    previous_failures = Column(Integer, default=0)
    consent_status = Column(Boolean, default=True)
    opt_out = Column(Boolean, default=False)
    dispute_status = Column(Boolean, default=False)
    hardship_status = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)

    # relationships
    transactions = relationship("Transaction", back_populates="customer")
    payment_events = relationship("PaymentEvent", back_populates="customer")
    checkout_events = relationship("CheckoutEvent", back_populates="customer")
    invoices = relationship("Invoice", back_populates="customer")
    recovery_cases = relationship("RecoveryCase", back_populates="customer")
    promises = relationship("PromiseToPay", back_populates="customer")
    mandates = relationship("MandateSchedule", back_populates="customer")


# ---------------------------------------------------------------------------
# Transaction
# ---------------------------------------------------------------------------
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(10), default="INR")
    payment_method = Column(String(50))
    status = Column(String(30))  # SUCCESS, FAILED, PENDING
    failure_reason = Column(String(200))
    gateway_reference = Column(String(200))
    created_at = Column(DateTime, default=_utcnow)

    customer = relationship("Customer", back_populates="transactions")


# ---------------------------------------------------------------------------
# PaymentEvent
# ---------------------------------------------------------------------------
class PaymentEvent(Base):
    __tablename__ = "payment_events"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(10), default="INR")
    payment_method = Column(String(50))
    failure_reason = Column(String(200))
    decline_code = Column(String(50))
    status = Column(String(30))  # FAILED, RETRIED, RECOVERED
    event_type = Column(String(50))  # failed_payment, subscription_renewal, upi_failure, etc.
    created_at = Column(DateTime, default=_utcnow)

    customer = relationship("Customer", back_populates="payment_events")
    transaction = relationship("Transaction")
    recovery_cases = relationship("RecoveryCase", back_populates="payment_event")


# ---------------------------------------------------------------------------
# CheckoutEvent
# ---------------------------------------------------------------------------
class CheckoutEvent(Base):
    __tablename__ = "checkout_events"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(10), default="INR")
    session_id = Column(String(200))
    payment_method = Column(String(50))
    abandonment_reason = Column(String(200))
    page_reached = Column(String(100))  # cart, payment_page, otp, etc.
    status = Column(String(30))  # ABANDONED, RECOVERED
    created_at = Column(DateTime, default=_utcnow)

    customer = relationship("Customer", back_populates="checkout_events")
    recovery_cases = relationship("RecoveryCase", back_populates="checkout_event")


# ---------------------------------------------------------------------------
# Invoice  (for B2B receivables)
# ---------------------------------------------------------------------------
class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    invoice_number = Column(String(100))
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(10), default="INR")
    issue_date = Column(DateTime)
    due_date = Column(DateTime)
    days_overdue = Column(Integer, default=0)
    dispute_flag = Column(Boolean, default=False)
    status = Column(String(30))  # PENDING, PAID, OVERDUE, DISPUTED
    created_at = Column(DateTime, default=_utcnow)

    customer = relationship("Customer", back_populates="invoices")
    recovery_cases = relationship("RecoveryCase", back_populates="invoice")
    promises = relationship("PromiseToPay", back_populates="invoice")


# ---------------------------------------------------------------------------
# RecoveryCase  — central entity linking risk event to recovery workflow
# ---------------------------------------------------------------------------
class RecoveryCase(Base):
    __tablename__ = "recovery_cases"

    id = Column(Integer, primary_key=True, index=True)
    # link to the source event (exactly one will be set)
    payment_event_id = Column(Integer, ForeignKey("payment_events.id"), nullable=True)
    checkout_event_id = Column(Integer, ForeignKey("checkout_events.id"), nullable=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)

    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    amount_at_risk = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(10), default="INR")
    recovery_type = Column(String(30))  # PAYMENT, CHECKOUT, RECEIVABLES
    root_cause = Column(String(100))
    confidence = Column(Float)
    evidence = Column(JSON, default=list)
    risk_score = Column(Float, default=0.0)
    recovery_probability = Column(Float, default=0.0)

    status = Column(String(30), default="PENDING")
    # PENDING, DIAGNOSED, IN_PROGRESS, RECOVERED, ESCALATED, STOPPED
    stop_reason = Column(String(200))
    attempt_count = Column(Integer, default=0)
    amount_recovered = Column(Numeric(12, 2), default=0)
    batch_run_id = Column(Integer, ForeignKey("batch_runs.id"), nullable=True)

    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    # relationships
    customer = relationship("Customer", back_populates="recovery_cases")
    payment_event = relationship("PaymentEvent", back_populates="recovery_cases")
    checkout_event = relationship("CheckoutEvent", back_populates="recovery_cases")
    invoice = relationship("Invoice", back_populates="recovery_cases")
    actions = relationship("RecoveryAction", back_populates="case", order_by="RecoveryAction.created_at")
    ledger_entries = relationship("RecoveryLedger", back_populates="case", order_by="RecoveryLedger.created_at")
    agent_decisions = relationship("AgentDecision", back_populates="case", order_by="AgentDecision.created_at")
    policy_checks = relationship("PolicyCheck", back_populates="case", order_by="PolicyCheck.created_at")
    batch_run = relationship("BatchRun", back_populates="cases")
    mandate_schedule = relationship("MandateSchedule", back_populates="case", uselist=False)


# ---------------------------------------------------------------------------
# RecoveryAction
# ---------------------------------------------------------------------------
class RecoveryAction(Base):
    __tablename__ = "recovery_actions"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("recovery_cases.id"), nullable=False)
    action_type = Column(String(50))
    # SMART_RETRY, PAYMENT_LINK, ALTERNATE_PAYMENT_METHOD, REMINDER,
    # HINGLISH_MESSAGE, PROMISE_TO_PAY, PAYMENT_PLAN, HUMAN_ESCALATION, STOP
    recovery_probability = Column(Float)
    intervention_cost = Column(Numeric(10, 2), default=0)
    expected_recovery_value = Column(Numeric(12, 2), default=0)
    incremental_recovery = Column(Float, default=0)
    baseline_probability = Column(Float, default=0)

    policy_status = Column(String(30))  # ALLOWED, DENIED, REQUIRES_APPROVAL
    policy_reason = Column(String(300))
    execution_result = Column(String(30))  # SUCCESS, FAILURE, PENDING, SKIPPED
    amount_recovered = Column(Numeric(12, 2), default=0)
    attempt_number = Column(Integer, default=1)
    message_content = Column(Text)
    message_language = Column(String(20))

    created_at = Column(DateTime, default=_utcnow)

    case = relationship("RecoveryCase", back_populates="actions")


# ---------------------------------------------------------------------------
# RecoveryLedger  — immutable audit trail
# ---------------------------------------------------------------------------
class RecoveryLedger(Base):
    __tablename__ = "recovery_ledger"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("recovery_cases.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    recovery_type = Column(String(30))
    amount_at_risk = Column(Numeric(12, 2))
    root_cause = Column(String(100))
    confidence = Column(Float)
    recommended_action = Column(String(50))
    selected_action = Column(String(50))
    recovery_probability = Column(Float)
    expected_recovery_value = Column(Numeric(12, 2))
    policy_result = Column(String(30))
    policy_reason = Column(String(300))
    execution_result = Column(String(30))
    amount_recovered = Column(Numeric(12, 2), default=0)
    status = Column(String(30))
    stop_reason = Column(String(200))
    agent_explanation = Column(Text)
    created_at = Column(DateTime, default=_utcnow)

    case = relationship("RecoveryCase", back_populates="ledger_entries")
    customer = relationship("Customer")


# ---------------------------------------------------------------------------
# PromiseToPay
# ---------------------------------------------------------------------------
class PromiseToPay(Base):
    __tablename__ = "promise_to_pay"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    case_id = Column(Integer, ForeignKey("recovery_cases.id"), nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(10), default="INR")
    promise_date = Column(DateTime, nullable=False)
    status = Column(String(30), default="PROMISED")  # PROMISED, PAID, MISSED, ESCALATED
    reminder_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    customer = relationship("Customer", back_populates="promises")
    invoice = relationship("Invoice", back_populates="promises")


# ---------------------------------------------------------------------------
# MandateSchedule — intelligent retry sequencer for recurring mandates
# ---------------------------------------------------------------------------
class MandateSchedule(Base):
    __tablename__ = "mandate_schedules"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    case_id = Column(Integer, ForeignKey("recovery_cases.id"), nullable=True)
    umrn = Column(String(100), unique=True, index=True, nullable=False)
    mandate_type = Column(String(50), nullable=False)  # UPI_AUTOPAY, E_NACH, CARD_SI
    bank_name = Column(String(100), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    max_amount = Column(Numeric(12, 2), nullable=False)
    frequency = Column(String(30), default="MONTHLY")
    status = Column(String(30), default="RESEQUENCED")  # ACTIVE, FAILED, RESEQUENCED, RECOVERED, REVOKED
    current_stage = Column(Integer, default=1)
    failure_reason = Column(String(200), default="mandate_fail")
    decline_code = Column(String(50), default="mandate_fail")
    pre_debit_notified = Column(Boolean, default=True)
    sequences = Column(JSON, default=list)
    next_presentation_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    customer = relationship("Customer", back_populates="mandates")
    case = relationship("RecoveryCase", back_populates="mandate_schedule")


# ---------------------------------------------------------------------------
# BatchRun
# ---------------------------------------------------------------------------
class BatchRun(Base):
    __tablename__ = "batch_runs"

    id = Column(Integer, primary_key=True, index=True)
    batch_size = Column(Integer, nullable=False)
    payment_pct = Column(Float, default=40)
    checkout_pct = Column(Float, default=30)
    receivables_pct = Column(Float, default=30)
    avg_transaction_value = Column(Numeric(12, 2), default=5000)
    failure_rate = Column(Float, default=0.6)
    status = Column(String(30), default="PENDING")
    # PENDING, GENERATING, PROCESSING, COMPLETED, FAILED

    events_processed = Column(Integer, default=0)
    revenue_at_risk = Column(Numeric(14, 2), default=0)
    revenue_recovered = Column(Numeric(14, 2), default=0)
    recovery_rate = Column(Float, default=0)
    actions_executed = Column(Integer, default=0)
    successful_actions = Column(Integer, default=0)
    escalations = Column(Integer, default=0)
    policy_stops = Column(Integer, default=0)

    # Baseline comparison
    baseline_recovered = Column(Numeric(14, 2), default=0)
    baseline_rate = Column(Float, default=0)
    baseline_actions = Column(Integer, default=0)
    incremental_recovered = Column(Numeric(14, 2), default=0)

    created_at = Column(DateTime, default=_utcnow)
    completed_at = Column(DateTime, nullable=True)

    cases = relationship("RecoveryCase", back_populates="batch_run")


# ---------------------------------------------------------------------------
# PolicyConfiguration  — dynamic policy values (NOT hardcoded)
# ---------------------------------------------------------------------------
class PolicyConfiguration(Base):
    __tablename__ = "policy_configuration"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(String(200), nullable=False)
    description = Column(String(500))
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


# ---------------------------------------------------------------------------
# AgentDecision  — reasoning trace for each case
# ---------------------------------------------------------------------------
class AgentDecision(Base):
    __tablename__ = "agent_decisions"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("recovery_cases.id"), nullable=False)
    reasoning = Column(Text)
    interventions_evaluated = Column(JSON)  # list of dicts
    selected_action = Column(String(50))
    why_selected = Column(Text)
    why_not_alternatives = Column(JSON)  # dict: action -> reason
    created_at = Column(DateTime, default=_utcnow)

    case = relationship("RecoveryCase", back_populates="agent_decisions")


# ---------------------------------------------------------------------------
# PolicyCheck  — log of each policy evaluation
# ---------------------------------------------------------------------------
class PolicyCheck(Base):
    __tablename__ = "policy_checks"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("recovery_cases.id"), nullable=False)
    action_type = Column(String(50))
    result = Column(String(30))  # ALLOWED, DENIED, REQUIRES_APPROVAL
    reason = Column(String(300))
    checked_at = Column(DateTime, default=_utcnow)
    created_at = Column(DateTime, default=_utcnow)

    case = relationship("RecoveryCase", back_populates="policy_checks")
