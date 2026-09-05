"""
Graph API router — queries existing SQL DB relationships to build a customer-centric
interactive entity relationship graph (Customer → Payments/Invoices → Methods → Failure Events).
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.database import get_db
from app.models.models import Customer, RecoveryCase
from app.schemas.schemas import GraphEdge, GraphNode, GraphResponse

router = APIRouter(prefix="/api/graph", tags=["Graph View"])


@router.get("/customer/{customer_id}", response_model=GraphResponse)
async def get_customer_graph(customer_id: int, db: AsyncSession = Depends(get_db)):
    query = (
        select(Customer)
        .options(
            selectinload(Customer.transactions),
            selectinload(Customer.payment_events),
            selectinload(Customer.checkout_events),
            selectinload(Customer.invoices),
            selectinload(Customer.recovery_cases),
            selectinload(Customer.promises),
        )
        .where(Customer.id == customer_id)
    )
    res = await db.execute(query)
    cust = res.scalar_one_or_none()
    if not cust:
        raise HTTPException(status_code=404, detail="Customer not found")

    nodes = []
    edges = []

    # Center node: Customer
    c_node_id = f"cust_{cust.id}"
    nodes.append(
        GraphNode(
            id=c_node_id,
            label=cust.name,
            type="customer",
            data={
                "ltv": float(cust.ltv or 0),
                "opt_out": cust.opt_out,
                "dispute": cust.dispute_status,
                "hardship": cust.hardship_status,
                "previous_payments": cust.previous_payments or 0,
            }
        )
    )

    # Recovery cases
    for rc in cust.recovery_cases:
        rc_id = f"rc_{rc.id}"
        nodes.append(
            GraphNode(
                id=rc_id,
                label=f"Case #{rc.id} ({rc.recovery_type})",
                type="case",
                data={
                    "amount": float(rc.amount_at_risk),
                    "status": rc.status,
                    "root_cause": rc.root_cause,
                    "confidence": rc.confidence,
                }
            )
        )
        edges.append(GraphEdge(source=c_node_id, target=rc_id, label="risk_exposure"))

    # Payment events
    for pe in cust.payment_events:
        pe_id = f"pe_{pe.id}"
        nodes.append(
            GraphNode(
                id=pe_id,
                label=f"Payment Fail (₹{float(pe.amount):,.0f})",
                type="payment_event",
                data={
                    "method": pe.payment_method,
                    "reason": pe.failure_reason,
                    "code": pe.decline_code,
                }
            )
        )
        edges.append(GraphEdge(source=c_node_id, target=pe_id, label="attempted_payment"))

    # Invoices
    for inv in cust.invoices:
        inv_id = f"inv_{inv.id}"
        nodes.append(
            GraphNode(
                id=inv_id,
                label=f"Invoice #{inv.invoice_number or inv.id}",
                type="invoice",
                data={
                    "amount": float(inv.amount),
                    "days_overdue": inv.days_overdue,
                    "status": inv.status,
                }
            )
        )
        edges.append(GraphEdge(source=c_node_id, target=inv_id, label="billed_to"))

    # Promises
    for p in cust.promises:
        p_id = f"ptp_{p.id}"
        nodes.append(
            GraphNode(
                id=p_id,
                label=f"Promise: ₹{float(p.amount):,.0f}",
                type="promise",
                data={
                    "date": p.promise_date.isoformat(),
                    "status": p.status,
                }
            )
        )
        edges.append(GraphEdge(source=c_node_id, target=p_id, label="committed_payment"))

    return GraphResponse(nodes=nodes, edges=edges)
