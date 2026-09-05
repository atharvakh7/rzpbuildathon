"""
Revenue Risk API router.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.schemas.schemas import RevenueRiskItem
from app.services.revenue_risk_engine import revenue_risk_engine

router = APIRouter(prefix="/api/revenue-risk", tags=["Revenue Risk"])


@router.get("", response_model=List[RevenueRiskItem])
async def get_revenue_risk(
    recovery_type: Optional[str] = Query(None, description="Filter by PAYMENT, CHECKOUT, RECEIVABLES or ALL"),
    status: Optional[str] = Query(None, description="Filter by status e.g. PENDING, RECOVERED, ESCALATED"),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Fetch dynamically prioritized list of revenue risk cases."""
    return await revenue_risk_engine.get_risk_queue(
        db=db,
        recovery_type=recovery_type,
        status=status,
        limit=limit,
        offset=offset,
    )
