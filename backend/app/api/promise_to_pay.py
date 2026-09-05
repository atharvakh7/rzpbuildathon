"""
Promise to Pay API router for overdue B2B receivables tracking.
"""

from typing import List
from datetime import datetime, timezone
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.database import get_db
from app.models.models import Customer, Invoice, PromiseToPay, RecoveryCase
from app.schemas.schemas import PromiseToPayItem, PromiseToPayRequest

router = APIRouter(prefix="/api/promise-to-pay", tags=["Promise to Pay"])


@router.get("", response_model=List[PromiseToPayItem])
async def list_promises(
    status: str = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(PromiseToPay)
        .options(selectinload(PromiseToPay.customer))
        .order_by(desc(PromiseToPay.created_at))
    )
    if status and status.upper() != "ALL":
        query = query.where(PromiseToPay.status == status.upper())

    query = query.limit(limit)
    res = await db.execute(query)
    records = res.scalars().all()

    items = []
    now = datetime.now(timezone.utc)
    for p in records:
        # Check if promise was missed
        p_date = p.promise_date.replace(tzinfo=timezone.utc) if p.promise_date.tzinfo is None else p.promise_date
        if p.status == "PROMISED" and p_date < now:
            p.status = "MISSED"

        items.append(
            PromiseToPayItem(
                id=p.id,
                customer_id=p.customer_id,
                customer_name=p.customer.name if p.customer else "Unknown",
                invoice_id=p.invoice_id,
                case_id=p.case_id,
                amount=float(p.amount),
                currency=p.currency or "INR",
                promise_date=p.promise_date,
                status=p.status,
                reminder_sent=p.reminder_sent or False,
                created_at=p.created_at,
            )
        )
    await db.commit()
    return items


@router.post("", response_model=PromiseToPayItem)
async def create_promise(payload: PromiseToPayRequest, db: AsyncSession = Depends(get_db)):
    p = PromiseToPay(
        customer_id=payload.customer_id,
        invoice_id=payload.invoice_id,
        case_id=payload.case_id,
        amount=Decimal(str(payload.amount)),
        promise_date=payload.promise_date,
        status="PROMISED",
    )
    db.add(p)
    await db.commit()
    await db.refresh(p)

    cust = (await db.execute(select(Customer).where(Customer.id == p.customer_id))).scalar_one_or_none()
    return PromiseToPayItem(
        id=p.id,
        customer_id=p.customer_id,
        customer_name=cust.name if cust else "Customer",
        invoice_id=p.invoice_id,
        case_id=p.case_id,
        amount=float(p.amount),
        currency=p.currency or "INR",
        promise_date=p.promise_date,
        status=p.status,
        reminder_sent=False,
        created_at=p.created_at,
    )


@router.put("/{promise_id}/status", response_model=PromiseToPayItem)
async def update_promise_status(promise_id: int, new_status: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(PromiseToPay)
        .options(selectinload(PromiseToPay.customer))
        .where(PromiseToPay.id == promise_id)
    )
    p = res.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Promise record not found")

    p.status = new_status.upper()
    await db.commit()

    return PromiseToPayItem(
        id=p.id,
        customer_id=p.customer_id,
        customer_name=p.customer.name if p.customer else "Customer",
        invoice_id=p.invoice_id,
        case_id=p.case_id,
        amount=float(p.amount),
        currency=p.currency or "INR",
        promise_date=p.promise_date,
        status=p.status,
        reminder_sent=p.reminder_sent or False,
        created_at=p.created_at,
    )
