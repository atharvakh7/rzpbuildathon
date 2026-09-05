"""
Recovery Ledger API router — queries immutable audit trail records.
NEVER populated with hardcoded fake entries.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.database import get_db
from app.models.models import RecoveryLedger
from app.schemas.schemas import LedgerEntry

router = APIRouter(prefix="/api/ledger", tags=["Recovery Ledger"])


@router.get("", response_model=List[LedgerEntry])
async def list_ledger_entries(
    case_id: Optional[int] = Query(None),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(RecoveryLedger)
        .options(selectinload(RecoveryLedger.customer))
        .order_by(desc(RecoveryLedger.created_at))
    )
    if case_id:
        query = query.where(RecoveryLedger.case_id == case_id)

    query = query.limit(limit).offset(offset)
    res = await db.execute(query)
    entries = res.scalars().all()

    items = []
    for e in entries:
        items.append(
            LedgerEntry(
                id=e.id,
                case_id=e.case_id,
                customer_id=e.customer_id,
                customer_name=e.customer.name if e.customer else "Unknown",
                recovery_type=e.recovery_type,
                amount_at_risk=float(e.amount_at_risk or 0),
                root_cause=e.root_cause,
                confidence=e.confidence,
                recommended_action=e.recommended_action,
                selected_action=e.selected_action,
                recovery_probability=e.recovery_probability,
                expected_recovery_value=float(e.expected_recovery_value or 0),
                policy_result=e.policy_result,
                policy_reason=e.policy_reason,
                execution_result=e.execution_result,
                amount_recovered=float(e.amount_recovered or 0),
                status=e.status,
                stop_reason=e.stop_reason,
                agent_explanation=e.agent_explanation,
                created_at=e.created_at,
            )
        )
    return items


@router.get("/{entry_id}", response_model=LedgerEntry)
async def get_ledger_entry(entry_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(RecoveryLedger)
        .options(selectinload(RecoveryLedger.customer))
        .where(RecoveryLedger.id == entry_id)
    )
    e = res.scalar_one_or_none()
    if not e:
        raise HTTPException(status_code=404, detail="Ledger entry not found")

    return LedgerEntry(
        id=e.id,
        case_id=e.case_id,
        customer_id=e.customer_id,
        customer_name=e.customer.name if e.customer else "Unknown",
        recovery_type=e.recovery_type,
        amount_at_risk=float(e.amount_at_risk or 0),
        root_cause=e.root_cause,
        confidence=e.confidence,
        recommended_action=e.recommended_action,
        selected_action=e.selected_action,
        recovery_probability=e.recovery_probability,
        expected_recovery_value=float(e.expected_recovery_value or 0),
        policy_result=e.policy_result,
        policy_reason=e.policy_reason,
        execution_result=e.execution_result,
        amount_recovered=float(e.amount_recovered or 0),
        status=e.status,
        stop_reason=e.stop_reason,
        agent_explanation=e.agent_explanation,
        created_at=e.created_at,
    )
