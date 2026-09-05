"""
Pydantic request / response models for the RecoverAI API.
These validate all data flowing in and out — no unvalidated payloads.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
class DashboardResponse(BaseModel):
    revenue_at_risk: float
    revenue_recovered: float
    recovery_rate: float
    active_cases: int
    recovered_cases: int
    escalated_cases: int
    stopped_cases: int
    total_cases: int
    pending_cases: int


# ---------------------------------------------------------------------------
# Revenue Risk
# ---------------------------------------------------------------------------
class RevenueRiskItem(BaseModel):
    id: int
    customer_id: int
    customer_name: str
    amount: float
    currency: str = "INR"
    recovery_type: str
    root_cause: Optional[str] = None
    risk_score: float = 0
    recovery_probability: float = 0
    recommended_action: Optional[str] = None
    status: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Intervention Analysis
# ---------------------------------------------------------------------------
class InterventionAnalysis(BaseModel):
    action: str
    recovery_probability: float
    intervention_cost: float
    expected_recovery_value: float
    incremental_recovery: float
    baseline_probability: float
    policy_status: str
    policy_reason: Optional[str] = None


# ---------------------------------------------------------------------------
# Recovery Case
# ---------------------------------------------------------------------------
class RecoveryCaseListItem(BaseModel):
    id: int
    customer_id: int
    customer_name: str
    amount_at_risk: float
    currency: str = "INR"
    recovery_type: str
    root_cause: Optional[str] = None
    confidence: Optional[float] = None
    status: str
    attempt_count: int
    amount_recovered: float
    created_at: datetime


class RecoveryCaseDetail(BaseModel):
    id: int
    customer_id: int
    customer_name: str
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_ltv: float = 0
    customer_tenure_months: int = 0
    customer_previous_payments: int = 0
    customer_previous_failures: int = 0
    customer_opt_out: bool = False
    customer_dispute_status: bool = False
    customer_hardship_status: bool = False
    amount_at_risk: float
    currency: str = "INR"
    recovery_type: str
    root_cause: Optional[str] = None
    confidence: Optional[float] = None
    evidence: list[str] = []
    risk_score: float = 0
    recovery_probability: float = 0
    status: str
    stop_reason: Optional[str] = None
    attempt_count: int
    amount_recovered: float
    payment_method: Optional[str] = None
    failure_reason: Optional[str] = None
    days_overdue: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    actions: list[RecoveryActionItem] = []
    timeline: list[TimelineEntry] = []


class RecoveryActionItem(BaseModel):
    id: int
    action_type: str
    recovery_probability: Optional[float] = None
    intervention_cost: float = 0
    expected_recovery_value: float = 0
    incremental_recovery: float = 0
    policy_status: Optional[str] = None
    policy_reason: Optional[str] = None
    execution_result: Optional[str] = None
    amount_recovered: float = 0
    attempt_number: int = 1
    message_content: Optional[str] = None
    message_language: Optional[str] = None
    created_at: datetime


class TimelineEntry(BaseModel):
    timestamp: datetime
    event: str
    detail: Optional[str] = None
    status: Optional[str] = None


# ---------------------------------------------------------------------------
# Analyze / Execute
# ---------------------------------------------------------------------------
class AnalyzeResponse(BaseModel):
    case_id: int
    root_cause: str
    confidence: float
    evidence: list[str]
    interventions: list[InterventionAnalysis]
    recommended_action: str
    agent_explanation: str
    why_not_alternatives: dict[str, str] = {}


class ExecuteRequest(BaseModel):
    action_type: Optional[str] = None  # if None, use recommended
    language: str = "english"


class ExecuteResponse(BaseModel):
    case_id: int
    action_type: str
    policy_result: str
    policy_reason: Optional[str] = None
    execution_result: str
    amount_recovered: float
    case_status: str
    stop_reason: Optional[str] = None
    message_content: Optional[str] = None
    agent_explanation: Optional[str] = None


class StopRequest(BaseModel):
    reason: str = "Manual stop by user"


# ---------------------------------------------------------------------------
# Batch
# ---------------------------------------------------------------------------
class BatchRunRequest(BaseModel):
    batch_size: int = Field(default=100, ge=10, le=2000)
    payment_pct: float = Field(default=40, ge=0, le=100)
    checkout_pct: float = Field(default=30, ge=0, le=100)
    receivables_pct: float = Field(default=30, ge=0, le=100)
    avg_transaction_value: float = Field(default=5000, ge=100)
    failure_rate: float = Field(default=0.6, ge=0.1, le=1.0)


class BatchStatusResponse(BaseModel):
    id: int
    batch_size: int
    status: str
    events_processed: int
    revenue_at_risk: float
    revenue_recovered: float
    recovery_rate: float
    actions_executed: int
    successful_actions: int
    escalations: int
    policy_stops: int
    baseline_recovered: float
    baseline_rate: float
    incremental_recovered: float
    created_at: datetime
    completed_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Ledger
# ---------------------------------------------------------------------------
class LedgerEntry(BaseModel):
    id: int
    case_id: int
    customer_id: int
    customer_name: Optional[str] = None
    recovery_type: str
    amount_at_risk: float
    root_cause: Optional[str] = None
    confidence: Optional[float] = None
    recommended_action: Optional[str] = None
    selected_action: Optional[str] = None
    recovery_probability: Optional[float] = None
    expected_recovery_value: Optional[float] = None
    policy_result: Optional[str] = None
    policy_reason: Optional[str] = None
    execution_result: Optional[str] = None
    amount_recovered: float = 0
    status: Optional[str] = None
    stop_reason: Optional[str] = None
    agent_explanation: Optional[str] = None
    created_at: datetime


# ---------------------------------------------------------------------------
# Policies
# ---------------------------------------------------------------------------
class PolicyConfigItem(BaseModel):
    key: str
    value: str
    description: Optional[str] = None


class PolicyConfigResponse(BaseModel):
    policies: list[PolicyConfigItem]


class PolicyConfigUpdateRequest(BaseModel):
    policies: list[PolicyConfigItem]


# ---------------------------------------------------------------------------
# Agent Permissions
# ---------------------------------------------------------------------------
class AgentPermissions(BaseModel):
    autonomous: list[str]
    requires_approval: list[str]
    never_allowed: list[str]


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------
class CategoryStat(BaseModel):
    category: str
    revenue_at_risk: float
    revenue_recovered: float
    recovery_rate: float
    cases: int


class InterventionStat(BaseModel):
    action: str
    count: int
    success_count: int
    success_rate: float
    total_recovered: float
    avg_recovered: float


class AnalyticsResponse(BaseModel):
    total_revenue_at_risk: float
    total_revenue_recovered: float
    overall_recovery_rate: float
    total_cases: int
    by_category: list[CategoryStat]
    by_intervention: list[InterventionStat]
    baseline_recovered: float
    baseline_rate: float
    recoverai_recovered: float
    recoverai_rate: float
    incremental_recovered: float
    escalation_rate: float
    avg_recovery_amount: float
    cost_per_recovery: float


# ---------------------------------------------------------------------------
# Simulator
# ---------------------------------------------------------------------------
class SimulatorGenerateRequest(BaseModel):
    batch_size: int = Field(default=100, ge=10, le=2000)
    payment_pct: float = Field(default=40, ge=0, le=100)
    checkout_pct: float = Field(default=30, ge=0, le=100)
    receivables_pct: float = Field(default=30, ge=0, le=100)
    avg_transaction_value: float = Field(default=5000, ge=100)
    failure_rate: float = Field(default=0.6, ge=0.1, le=1.0)


class SimulatorGenerateResponse(BaseModel):
    message: str
    customers_created: int
    payment_events: int
    checkout_events: int
    invoices: int
    recovery_cases: int


# ---------------------------------------------------------------------------
# Promise to Pay
# ---------------------------------------------------------------------------
class PromiseToPayRequest(BaseModel):
    customer_id: int
    invoice_id: int
    case_id: Optional[int] = None
    amount: float
    promise_date: datetime


class PromiseToPayItem(BaseModel):
    id: int
    customer_id: int
    customer_name: Optional[str] = None
    invoice_id: int
    case_id: Optional[int] = None
    amount: float
    currency: str = "INR"
    promise_date: datetime
    status: str
    reminder_sent: bool
    created_at: datetime


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------
class GraphNode(BaseModel):
    id: str
    label: str
    type: str  # customer, subscription, payment, payment_method, failure, invoice, promise
    data: dict[str, Any] = {}


class GraphEdge(BaseModel):
    source: str
    target: str
    label: Optional[str] = None


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


# ---------------------------------------------------------------------------
# Mandate Scheduler & Sequencer
# ---------------------------------------------------------------------------
class MandateSequenceStage(BaseModel):
    stage: int
    title: str
    scheduled_time: str
    clearing_window: str
    liquidity_probability: float
    channel: str
    status: str  # COMPLETED, IN_PROGRESS, SCHEDULED, SKIPPED
    result: Optional[str] = None  # SUCCESS, FAILED, PENDING
    notes: Optional[str] = None


class MandateScheduleItem(BaseModel):
    id: int
    customer_id: int
    customer_name: str
    customer_phone: Optional[str] = None
    case_id: Optional[int] = None
    umrn: str
    mandate_type: str
    bank_name: str
    amount: float
    max_amount: float
    frequency: str
    status: str
    current_stage: int
    failure_reason: str
    decline_code: str
    pre_debit_notified: bool
    next_presentation_at: Optional[datetime] = None
    created_at: datetime


class MandateScheduleDetail(MandateScheduleItem):
    sequences: list[MandateSequenceStage] = []
    case_status: Optional[str] = None
    case_amount_at_risk: Optional[float] = None


class PresentMandateRequest(BaseModel):
    override_success: Optional[bool] = None


class PresentMandateResponse(BaseModel):
    success: bool
    mandate_id: int
    umrn: str
    stage: int
    action_taken: str
    clearing_window: str
    amount_recovered: float
    new_status: str
    message: str


class RescheduleMandateRequest(BaseModel):
    target_stage: int
    new_scheduled_time: Optional[datetime] = None
    clearing_window: Optional[str] = None
