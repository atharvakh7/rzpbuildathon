"""
Simulator API router for generating synthetic datasets or performing hard demo resets.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.schemas.schemas import SimulatorGenerateRequest, SimulatorGenerateResponse
from app.simulation.data_generator import generate_dataset, reset_demo

router = APIRouter(prefix="/api/simulator", tags=["Simulator"])


@router.post("/generate", response_model=SimulatorGenerateResponse)
async def generate_simulated_data(
    payload: SimulatorGenerateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate new synthetic cases and persist to DB.
    """
    res = await generate_dataset(
        db=db,
        batch_size=payload.batch_size,
        payment_pct=payload.payment_pct,
        checkout_pct=payload.checkout_pct,
        receivables_pct=payload.receivables_pct,
        avg_transaction_value=payload.avg_transaction_value,
        failure_rate=payload.failure_rate,
    )
    await db.commit()

    return SimulatorGenerateResponse(
        message=f"Successfully generated {res['recovery_cases']} new recovery risk cases in database.",
        customers_created=res["customers_created"],
        payment_events=res["payment_events"],
        checkout_events=res["checkout_events"],
        invoices=res["invoices"],
        recovery_cases=res["recovery_cases"],
    )


@router.post("/reset")
async def reset_demo_data(db: AsyncSession = Depends(get_db)):
    """
    RESET DEMO — wipes out all demo records, generates fresh seed data and default policies.
    """
    await reset_demo(db)
    return {"message": "Demo state completely reset and re-seeded in database."}
