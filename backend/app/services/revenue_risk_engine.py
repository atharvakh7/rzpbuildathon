"""
Revenue Risk Engine — aggregates, monitors, and scores revenue at risk across
payments, checkouts, and receivables.
"""

from typing import List
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import RecoveryCase
from app.schemas.schemas import RevenueRiskItem


class RevenueRiskEngine:
    async def get_risk_queue(
        self,
        db: AsyncSession,
        recovery_type: str | None = None,
        status: str | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> List[RevenueRiskItem]:
        query = (
            select(RecoveryCase)
            .options(
                selectinload(RecoveryCase.customer),
                selectinload(RecoveryCase.actions),
            )
            .order_by(desc(RecoveryCase.amount_at_risk))
        )

        if recovery_type and recovery_type.upper() != "ALL":
            query = query.where(RecoveryCase.recovery_type == recovery_type.upper())
        if status and status.upper() != "ALL":
            query = query.where(RecoveryCase.status == status.upper())

        query = query.limit(limit).offset(offset)
        result = await db.execute(query)
        cases = result.scalars().all()

        items = []
        for c in cases:
            rec_action = c.actions[-1].action_type if c.actions else None
            items.append(
                RevenueRiskItem(
                    id=c.id,
                    customer_id=c.customer_id,
                    customer_name=c.customer.name if c.customer else "Unknown",
                    amount=float(c.amount_at_risk),
                    currency=c.currency or "INR",
                    recovery_type=c.recovery_type,
                    root_cause=c.root_cause,
                    risk_score=c.risk_score or 0.0,
                    recovery_probability=c.recovery_probability or 0.0,
                    recommended_action=rec_action,
                    status=c.status,
                    created_at=c.created_at,
                )
            )
        return items


revenue_risk_engine = RevenueRiskEngine()
