"""
Dashboard metrics endpoint.
CRITICAL: All numbers are dynamically queried and calculated from DB records.
NEVER hardcode metrics!
"""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.models.models import RecoveryCase
from app.schemas.schemas import DashboardResponse

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("", response_model=DashboardResponse)
async def get_dashboard_metrics(db: AsyncSession = Depends(get_db)):
    """
    Compute real-time summary statistics from DB tables.
    """
    # Total revenue at risk
    risk_query = select(func.coalesce(func.sum(RecoveryCase.amount_at_risk), 0))
    total_risk = float((await db.execute(risk_query)).scalar() or 0.0)

    # Revenue recovered (sum of amount_recovered where status = RECOVERED)
    recovered_query = select(
        func.coalesce(func.sum(RecoveryCase.amount_recovered), 0)
    ).where(RecoveryCase.status == "RECOVERED")
    total_recovered = float((await db.execute(recovered_query)).scalar() or 0.0)

    # Overall recovery rate
    recovery_rate = round((total_recovered / total_risk * 100), 2) if total_risk > 0 else 0.0

    # Case status counts
    total_cases_query = select(func.count(RecoveryCase.id))
    total_cases = (await db.execute(total_cases_query)).scalar() or 0

    active_cases_query = select(func.count(RecoveryCase.id)).where(
        RecoveryCase.status.in_(["PENDING", "DIAGNOSED", "IN_PROGRESS"])
    )
    active_cases = (await db.execute(active_cases_query)).scalar() or 0

    pending_cases_query = select(func.count(RecoveryCase.id)).where(RecoveryCase.status == "PENDING")
    pending_cases = (await db.execute(pending_cases_query)).scalar() or 0

    recovered_cases_query = select(func.count(RecoveryCase.id)).where(RecoveryCase.status == "RECOVERED")
    recovered_cases = (await db.execute(recovered_cases_query)).scalar() or 0

    escalated_cases_query = select(func.count(RecoveryCase.id)).where(RecoveryCase.status == "ESCALATED")
    escalated_cases = (await db.execute(escalated_cases_query)).scalar() or 0

    stopped_cases_query = select(func.count(RecoveryCase.id)).where(RecoveryCase.status == "STOPPED")
    stopped_cases = (await db.execute(stopped_cases_query)).scalar() or 0

    return DashboardResponse(
        revenue_at_risk=round(total_risk, 2),
        revenue_recovered=round(total_recovered, 2),
        recovery_rate=recovery_rate,
        active_cases=active_cases,
        recovered_cases=recovered_cases,
        escalated_cases=escalated_cases,
        stopped_cases=stopped_cases,
        total_cases=total_cases,
        pending_cases=pending_cases,
    )
