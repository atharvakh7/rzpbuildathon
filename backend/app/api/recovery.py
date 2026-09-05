"""
Recovery Cases API router:
- List & retrieve detailed case information
- Trigger autonomous diagnosis & ERV intervention evaluation
- Execute interventions
- Manually approve or stop workflows
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.database import get_db
from app.models.models import Customer, RecoveryAction, RecoveryCase, RecoveryLedger
from app.schemas.schemas import (
    AnalyzeResponse,
    ExecuteRequest,
    ExecuteResponse,
    RecoveryActionItem,
    RecoveryCaseDetail,
    RecoveryCaseListItem,
    StopRequest,
    TimelineEntry,
)
from app.services.recovery_agent import recovery_agent

router = APIRouter(prefix="/api/recovery-cases", tags=["Recovery Cases"])


@router.get("", response_model=List[RecoveryCaseListItem])
async def list_recovery_cases(
    status: Optional[str] = Query(None),
    recovery_type: Optional[str] = Query(None),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(RecoveryCase)
        .options(selectinload(RecoveryCase.customer))
        .order_by(desc(RecoveryCase.id))
    )
    if status and status.upper() != "ALL":
        query = query.where(RecoveryCase.status == status.upper())
    if recovery_type and recovery_type.upper() != "ALL":
        query = query.where(RecoveryCase.recovery_type == recovery_type.upper())

    query = query.limit(limit).offset(offset)
    res = await db.execute(query)
    cases = res.scalars().all()

    items = []
    for c in cases:
        items.append(
            RecoveryCaseListItem(
                id=c.id,
                customer_id=c.customer_id,
                customer_name=c.customer.name if c.customer else "Unknown",
                amount_at_risk=float(c.amount_at_risk),
                currency=c.currency or "INR",
                recovery_type=c.recovery_type,
                root_cause=c.root_cause,
                confidence=c.confidence,
                status=c.status,
                attempt_count=c.attempt_count or 0,
                amount_recovered=float(c.amount_recovered or 0.0),
                created_at=c.created_at,
            )
        )
    return items


@router.get("/{case_id}", response_model=RecoveryCaseDetail)
async def get_recovery_case_detail(case_id: int, db: AsyncSession = Depends(get_db)):
    query = (
        select(RecoveryCase)
        .options(
            selectinload(RecoveryCase.customer),
            selectinload(RecoveryCase.payment_event),
            selectinload(RecoveryCase.checkout_event),
            selectinload(RecoveryCase.invoice),
            selectinload(RecoveryCase.actions),
            selectinload(RecoveryCase.ledger_entries),
        )
        .where(RecoveryCase.id == case_id)
    )
    res = await db.execute(query)
    case = res.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Recovery case not found")

    customer = case.customer

    # Build timeline from actions + ledger
    timeline: List[TimelineEntry] = [
        TimelineEntry(
            timestamp=case.created_at,
            event="Revenue Risk Detected",
            detail=f"{case.recovery_type} failure detected for INR {float(case.amount_at_risk):,.2f}",
            status="DETECTED"
        )
    ]
    if case.root_cause:
        timeline.append(
            TimelineEntry(
                timestamp=case.updated_at or case.created_at,
                event="Root Cause Diagnosed",
                detail=f"{case.root_cause.replace('_', ' ').title()} ({int((case.confidence or 0.8)*100)}% confidence)",
                status="DIAGNOSED"
            )
        )

    for action in case.actions:
        timeline.append(
            TimelineEntry(
                timestamp=action.created_at,
                event=f"Executed {action.action_type.replace('_', ' ').title()}",
                detail=f"Outcome: {action.execution_result} (ERV: ₹{float(action.expected_recovery_value or 0):,.2f})",
                status=action.execution_result
            )
        )

    action_items = [
        RecoveryActionItem(
            id=a.id,
            action_type=a.action_type,
            recovery_probability=a.recovery_probability,
            intervention_cost=float(a.intervention_cost or 0),
            expected_recovery_value=float(a.expected_recovery_value or 0),
            incremental_recovery=float(a.incremental_recovery or 0),
            policy_status=a.policy_status,
            policy_reason=a.policy_reason,
            execution_result=a.execution_result,
            amount_recovered=float(a.amount_recovered or 0),
            attempt_number=a.attempt_number or 1,
            message_content=a.message_content,
            message_language=a.message_language,
            created_at=a.created_at,
        )
        for a in case.actions
    ]

    return RecoveryCaseDetail(
        id=case.id,
        customer_id=case.customer_id,
        customer_name=customer.name if customer else "Customer",
        customer_email=customer.email if customer else None,
        customer_phone=customer.phone if customer else None,
        customer_ltv=float(customer.ltv or 0) if customer else 0,
        customer_tenure_months=customer.tenure_months or 0 if customer else 0,
        customer_previous_payments=customer.previous_payments or 0 if customer else 0,
        customer_previous_failures=customer.previous_failures or 0 if customer else 0,
        customer_opt_out=customer.opt_out if customer else False,
        customer_dispute_status=customer.dispute_status if customer else False,
        customer_hardship_status=customer.hardship_status if customer else False,
        amount_at_risk=float(case.amount_at_risk),
        currency=case.currency or "INR",
        recovery_type=case.recovery_type,
        root_cause=case.root_cause,
        confidence=case.confidence,
        evidence=case.evidence or [],
        risk_score=case.risk_score or 0.0,
        recovery_probability=case.recovery_probability or 0.0,
        status=case.status,
        stop_reason=case.stop_reason,
        attempt_count=case.attempt_count or 0,
        amount_recovered=float(case.amount_recovered or 0),
        payment_method=case.payment_event.payment_method if case.payment_event else None,
        failure_reason=case.payment_event.failure_reason if case.payment_event else (
            case.checkout_event.abandonment_reason if case.checkout_event else None
        ),
        days_overdue=case.invoice.days_overdue if case.invoice else None,
        created_at=case.created_at,
        updated_at=case.updated_at,
        actions=action_items,
        timeline=timeline,
    )


@router.post("/{case_id}/analyze", response_model=AnalyzeResponse)
async def analyze_case(case_id: int, db: AsyncSession = Depends(get_db)):
    """
    Agentic step: Diagnoses root cause, evaluates candidate interventions via ERV,
    runs policy guardrail checks, and generates explanation.
    """
    try:
        data = await recovery_agent.analyze_case(db=db, case_id=case_id)
        await db.commit()
        return data
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{case_id}/execute", response_model=ExecuteResponse)
async def execute_case_intervention(
    case_id: int,
    payload: ExecuteRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Execute selected or recommended intervention.
    Enforces deterministic policy guardrails and registers audit ledger entries.
    """
    try:
        res = await recovery_agent.run_agent_on_case(
            db=db,
            case_id=case_id,
            forced_action=payload.action_type,
            language=payload.language or "english",
        )
        await db.commit()
        return res
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{case_id}/approve", response_model=ExecuteResponse)
async def approve_case(case_id: int, db: AsyncSession = Depends(get_db)):
    """Human approval for high-value / hardship / restricted action."""
    try:
        # Find latest pending decision or analyze
        analysis = await recovery_agent.analyze_case(db=db, case_id=case_id)
        # Execute the highest ERV intervention
        res = await recovery_agent.run_agent_on_case(
            db=db,
            case_id=case_id,
            forced_action=analysis["recommended_action"],
        )
        await db.commit()
        return res
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{case_id}/stop")
async def stop_case(case_id: int, payload: StopRequest, db: AsyncSession = Depends(get_db)):
    """Stop the recovery workflow for a case."""
    res = await db.execute(select(RecoveryCase).where(RecoveryCase.id == case_id))
    case = res.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    case.status = "STOPPED"
    case.stop_reason = payload.reason
    await db.commit()
    return {"status": "STOPPED", "case_id": case_id, "stop_reason": payload.reason}
