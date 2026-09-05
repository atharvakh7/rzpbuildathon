"""
Policies & Agent Permissions API router.
Supports dynamic editing of policy guardrail thresholds in the database!
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.models.models import PolicyConfiguration
from app.schemas.schemas import (
    AgentPermissions,
    PolicyConfigItem,
    PolicyConfigResponse,
    PolicyConfigUpdateRequest,
)

router = APIRouter(prefix="/api/policies", tags=["Policies"])


@router.get("", response_model=PolicyConfigResponse)
async def get_policies(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(PolicyConfiguration).order_by(PolicyConfiguration.id))
    rows = res.scalars().all()
    return PolicyConfigResponse(
        policies=[
            PolicyConfigItem(key=r.key, value=r.value, description=r.description)
            for r in rows
        ]
    )


@router.put("", response_model=PolicyConfigResponse)
async def update_policies(payload: PolicyConfigUpdateRequest, db: AsyncSession = Depends(get_db)):
    for item in payload.policies:
        res = await db.execute(
            select(PolicyConfiguration).where(PolicyConfiguration.key == item.key)
        )
        existing = res.scalar_one_or_none()
        if existing:
            existing.value = item.value
            if item.description:
                existing.description = item.description
        else:
            db.add(PolicyConfiguration(key=item.key, value=item.value, description=item.description))
    await db.commit()

    # Re-fetch
    res = await db.execute(select(PolicyConfiguration).order_by(PolicyConfiguration.id))
    rows = res.scalars().all()
    return PolicyConfigResponse(
        policies=[
            PolicyConfigItem(key=r.key, value=r.value, description=r.description)
            for r in rows
        ]
    )


@router.get("/permissions", response_model=AgentPermissions)
async def get_agent_permissions():
    """
    Returns boundaries of agent autonomy.
    """
    return AgentPermissions(
        autonomous=[
            "Smart Payment Retry (within max retry limits)",
            "Dynamic Payment Link Generation & Delivery",
            "Multi-channel Recovery Notifications (SMS, WhatsApp, Email)",
            "Hinglish / English Contextual Communication",
            "Automatic Status Transitions & Audit Ledger Logging",
            "Workflow Termination upon Successful Settlement",
        ],
        requires_approval=[
            "High-Value Recovery Cases (> Configured Threshold)",
            "Multi-part Restructured Payment Plans",
            "Overdue Accounts with Active Inquiries",
            "Cases flagged for Financial Hardship",
            "Recovery Interventions exceeding standard daily contact frequencies",
        ],
        never_allowed=[
            "Continue automated recovery after Customer Opt-Out",
            "Retry charges on Accounts with Confirmed Bank Fraud or Active Chargeback Disputes",
            "Exceed maximum retry limits or violate retry cooldown windows",
            "Violate maximum daily communication frequency caps",
            "Execute negative Expected Recovery Value interventions",
        ],
    )
