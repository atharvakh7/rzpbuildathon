"""
Mandate Retry Sequencer API.
Manages eNACH, UPI AutoPay, and Card SI recurring payment retry schedules,
clearing session windows, RBI pre-debit notifications, and presentation executions.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import random
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import flag_modified
import copy

from app.database.database import get_db
from app.models.models import Customer, MandateSchedule, RecoveryCase, RecoveryLedger, RecoveryAction
from app.schemas.schemas import (
    MandateScheduleDetail,
    MandateScheduleItem,
    PresentMandateRequest,
    PresentMandateResponse,
    RescheduleMandateRequest,
)

router = APIRouter(prefix="/api/mandates", tags=["Mandate Sequencer"])


def _utcnow():
    return datetime.now(timezone.utc)


@router.get("/stats")
async def get_mandate_stats(db: AsyncSession = Depends(get_db)):
    """Summary KPI metrics for recurring mandate retry sequencer."""
    res = await db.execute(select(MandateSchedule))
    mandates = res.scalars().all()

    total = len(mandates)
    at_risk = sum(1 for m in mandates if m.status in ("FAILED", "RESEQUENCED"))
    recovered = sum(1 for m in mandates if m.status == "RECOVERED")
    recovered_amount = sum(float(m.amount) for m in mandates if m.status == "RECOVERED")
    total_risk_amount = sum(float(m.amount) for m in mandates)
    recovery_rate = (recovered / total * 100) if total > 0 else 0.0

    return {
        "total_mandates": total,
        "at_risk_mandates": at_risk,
        "recovered_mandates": recovered,
        "recovered_amount": round(recovered_amount, 2),
        "total_risk_amount": round(total_risk_amount, 2),
        "recovery_rate": round(recovery_rate, 1),
        "next_clearing_window": "Morning NACH Session (10:00 - 11:30 AM IST)",
        "active_clearing_bank": "NPCI / RBI e-Mandate Switch",
    }


@router.get("", response_model=List[MandateScheduleItem])
async def list_mandates(
    status: Optional[str] = Query(None),
    mandate_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List all mandate schedules with customer data."""
    query = (
        select(MandateSchedule)
        .options(selectinload(MandateSchedule.customer))
        .order_by(desc(MandateSchedule.id))
    )

    if status:
        query = query.where(MandateSchedule.status == status.upper())
    if mandate_type:
        query = query.where(MandateSchedule.mandate_type == mandate_type.upper())

    result = await db.execute(query)
    mandates = result.scalars().all()

    items = []
    for m in mandates:
        items.append(
            MandateScheduleItem(
                id=m.id,
                customer_id=m.customer_id,
                customer_name=m.customer.name if m.customer else "Unknown",
                customer_phone=m.customer.phone if m.customer else None,
                case_id=m.case_id,
                umrn=m.umrn,
                mandate_type=m.mandate_type,
                bank_name=m.bank_name,
                amount=float(m.amount),
                max_amount=float(m.max_amount),
                frequency=m.frequency,
                status=m.status,
                current_stage=m.current_stage,
                failure_reason=m.failure_reason,
                decline_code=m.decline_code,
                pre_debit_notified=m.pre_debit_notified,
                next_presentation_at=m.next_presentation_at,
                created_at=m.created_at,
            )
        )
    return items


@router.get("/{mandate_id}", response_model=MandateScheduleDetail)
async def get_mandate_detail(
    mandate_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get comprehensive mandate retry schedule with sequences and case info."""
    query = (
        select(MandateSchedule)
        .options(
            selectinload(MandateSchedule.customer),
            selectinload(MandateSchedule.case),
        )
        .where(MandateSchedule.id == mandate_id)
    )
    res = await db.execute(query)
    m = res.scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="Mandate schedule not found")

    return MandateScheduleDetail(
        id=m.id,
        customer_id=m.customer_id,
        customer_name=m.customer.name if m.customer else "Unknown",
        customer_phone=m.customer.phone if m.customer else None,
        case_id=m.case_id,
        umrn=m.umrn,
        mandate_type=m.mandate_type,
        bank_name=m.bank_name,
        amount=float(m.amount),
        max_amount=float(m.max_amount),
        frequency=m.frequency,
        status=m.status,
        current_stage=m.current_stage,
        failure_reason=m.failure_reason,
        decline_code=m.decline_code,
        pre_debit_notified=m.pre_debit_notified,
        next_presentation_at=m.next_presentation_at,
        created_at=m.created_at,
        sequences=m.sequences or [],
        case_status=m.case.status if m.case else None,
        case_amount_at_risk=float(m.case.amount_at_risk) if m.case else None,
    )


@router.post("/{mandate_id}/present-now", response_model=PresentMandateResponse)
async def present_mandate_now(
    mandate_id: int,
    payload: Optional[PresentMandateRequest] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Execute an immediate presentation for the current scheduled sequence stage.
    Dynamically adjusts sequence states, mutates DB records, and logs into the recovery ledger.
    """
    query = (
        select(MandateSchedule)
        .options(
            selectinload(MandateSchedule.customer),
            selectinload(MandateSchedule.case),
        )
        .where(MandateSchedule.id == mandate_id)
    )
    res = await db.execute(query)
    m = res.scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="Mandate schedule not found")

    if m.status == "RECOVERED":
        return PresentMandateResponse(
            success=True,
            mandate_id=m.id,
            umrn=m.umrn,
            stage=m.current_stage,
            action_taken="NOOP",
            clearing_window="Already Settled",
            amount_recovered=float(m.amount),
            new_status="RECOVERED",
            message="Mandate has already been successfully collected.",
        )

    sequences = copy.deepcopy(m.sequences or [])
    curr_stage_idx = max(0, min(len(sequences) - 1, m.current_stage - 1))
    current_seq = sequences[curr_stage_idx] if sequences else {
        "stage": 1,
        "title": "Stage 1: Soft Failure Cooldown & Re-presentation",
        "scheduled_time": _utcnow().isoformat(),
        "clearing_window": "Morning NACH Session (10:00 - 11:30 AM)",
        "liquidity_probability": 0.75,
        "channel": "eNACH Batch",
        "status": "IN_PROGRESS",
    }

    # Determine success
    if payload and payload.override_success is not None:
        success = payload.override_success
    else:
        prob = current_seq.get("liquidity_probability", 0.70)
        success = random.random() < prob

    amount = float(m.amount)

    if success:
        current_seq["status"] = "COMPLETED"
        current_seq["result"] = "SUCCESS"
        current_seq["notes"] = f"Successfully debited INR {amount:,.2f} during {current_seq.get('clearing_window')}."
        m.status = "RECOVERED"
        m.next_presentation_at = None

        # If linked to a recovery case, mark case as recovered and append to ledger
        if m.case:
            m.case.status = "RECOVERED"
            m.case.amount_recovered = Decimal(str(amount))
            m.case.stop_reason = f"Mandate debit cleared on UMRN {m.umrn}"

            action = RecoveryAction(
                case_id=m.case.id,
                action_type="SMART_RETRY",
                recovery_probability=float(current_seq.get("liquidity_probability", 0.8)),
                intervention_cost=Decimal("10.00"),
                expected_recovery_value=Decimal(str(round(amount * 0.8 - 10, 2))),
                incremental_recovery=0.25,
                policy_status="ALLOWED",
                policy_reason="Mandate sequencer scheduled execution within bank clearing window.",
                execution_result="SUCCESS",
                amount_recovered=Decimal(str(amount)),
                attempt_number=(m.case.attempt_count or 0) + 1,
                message_content=f"Mandate debit successful for INR {amount:,.2f} via {m.bank_name}.",
                message_language="system",
            )
            db.add(action)

            ledger = RecoveryLedger(
                case_id=m.case.id,
                customer_id=m.customer_id,
                recovery_type="PAYMENT",
                amount_at_risk=m.case.amount_at_risk,
                root_cause=m.failure_reason,
                confidence=0.88,
                recommended_action="SMART_RETRY",
                selected_action="SMART_RETRY",
                recovery_probability=float(current_seq.get("liquidity_probability", 0.8)),
                expected_recovery_value=Decimal(str(round(amount * 0.8 - 10, 2))),
                policy_result="ALLOWED",
                policy_reason="Sequencer clearing window alignment.",
                execution_result="SUCCESS",
                amount_recovered=Decimal(str(amount)),
                status="RECOVERED",
                stop_reason="Mandate collected",
                agent_explanation=f"Mandate presented and honored during {current_seq.get('clearing_window')}.",
            )
            db.add(ledger)

        message = f"Mandate debit succeeded! Collected INR {amount:,.2f} from {m.bank_name}."

    else:
        current_seq["status"] = "COMPLETED"
        current_seq["result"] = "FAILED"
        current_seq["notes"] = f"Issuer returned decline during {current_seq.get('clearing_window')}. Moving to next sequence."

        # Advance to next stage if available
        if m.current_stage < len(sequences):
            m.current_stage += 1
            next_seq = sequences[m.current_stage - 1]
            next_seq["status"] = "IN_PROGRESS"
            m.status = "RESEQUENCED"
            m.next_presentation_at = _utcnow() + timedelta(days=2)
            message = f"Debit attempt failed. Sequencer advanced to Stage {m.current_stage} ({next_seq.get('title')})."
        else:
            m.status = "FAILED"
            m.next_presentation_at = None
            if m.case:
                m.case.status = "ESCALATED"
                m.case.stop_reason = "All 4 mandate sequence presentations exhausted without clearance."
            message = "Debit attempt failed. All retry sequence stages exhausted; mandate flagged for human escalation."

    await db.execute(
        update(MandateSchedule)
        .where(MandateSchedule.id == m.id)
        .values(
            status=m.status,
            current_stage=m.current_stage,
            next_presentation_at=m.next_presentation_at,
            sequences=sequences,
        )
    )
    await db.commit()

    return PresentMandateResponse(
        success=success,
        mandate_id=m.id,
        umrn=m.umrn,
        stage=current_seq.get("stage", 1),
        action_taken="MANDATE_PRESENTATION",
        clearing_window=current_seq.get("clearing_window", "Session"),
        amount_recovered=amount if success else 0.0,
        new_status=m.status,
        message=message,
    )


@router.post("/{mandate_id}/reschedule")
async def reschedule_mandate(
    mandate_id: int,
    payload: RescheduleMandateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Reschedule the next presentation window or target stage for liquidity matching."""
    query = select(MandateSchedule).where(MandateSchedule.id == mandate_id)
    res = await db.execute(query)
    m = res.scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="Mandate schedule not found")

    sequences = list(m.sequences or [])
    m.current_stage = payload.target_stage
    if payload.new_scheduled_time:
        m.next_presentation_at = payload.new_scheduled_time
    else:
        m.next_presentation_at = _utcnow() + timedelta(days=1)

    for s in sequences:
        if s.get("stage") == payload.target_stage:
            s["status"] = "IN_PROGRESS"
            if payload.clearing_window:
                s["clearing_window"] = payload.clearing_window
        elif s.get("stage") > payload.target_stage:
            s["status"] = "SCHEDULED"

    await db.execute(
        update(MandateSchedule)
        .where(MandateSchedule.id == m.id)
        .values(
            status="RESEQUENCED",
            current_stage=m.current_stage,
            next_presentation_at=m.next_presentation_at,
            sequences=sequences,
        )
    )
    await db.commit()

    return {
        "status": "success",
        "message": f"Mandate {m.umrn} rescheduled to Stage {payload.target_stage} successfully.",
        "next_presentation_at": m.next_presentation_at,
    }
