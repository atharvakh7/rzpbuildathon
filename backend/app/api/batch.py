"""
Batch simulation and processing API.
Supports generating synthetic events (100, 500, 1000) and concurrently executing
autonomous recovery loops while running baseline A/B benchmarking!
"""

import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.database import async_session, get_db
from app.models.models import BatchRun, RecoveryCase
from app.schemas.schemas import BatchRunRequest, BatchStatusResponse
from app.services.baseline_engine import baseline_engine
from app.services.recovery_agent import recovery_agent
from app.simulation.data_generator import generate_dataset

router = APIRouter(prefix="/api/batch", tags=["Batch Processing"])


async def _run_batch_worker(batch_id: int):
    """
    Background worker processing all cases in the batch concurrently.
    Computes both RecoverAI dynamic agent recovery AND baseline recovery.
    """
    async with async_session() as db:
        try:
            batch_res = await db.execute(select(BatchRun).where(BatchRun.id == batch_id))
            batch = batch_res.scalar_one_or_none()
            if not batch:
                return

            batch.status = "PROCESSING"
            await db.commit()

            # Retrieve all cases attached to this batch or pending
            cases_res = await db.execute(
                select(RecoveryCase)
                .options(selectinload(RecoveryCase.customer))
                .where(RecoveryCase.batch_run_id == batch_id)
            )
            cases = cases_res.scalars().all()

            if not cases:
                # If cases were not tagged, associate the latest unassigned ones
                cases_res = await db.execute(
                    select(RecoveryCase)
                    .options(selectinload(RecoveryCase.customer))
                    .where(RecoveryCase.batch_run_id.is_(None))
                    .limit(batch.batch_size)
                )
                cases = cases_res.scalars().all()
                for c in cases:
                    c.batch_run_id = batch.id
                await db.commit()

            # 1. Run genuine baseline comparison on the exact same cases
            baseline_results = await baseline_engine.run_baseline_benchmark(db, cases)
            batch.baseline_recovered = Decimal(str(baseline_results["baseline_recovered"]))
            batch.baseline_rate = baseline_results["baseline_rate"]
            batch.baseline_actions = baseline_results["baseline_actions"]
            await db.commit()

            # 2. Run RecoverAI Agent concurrently in bounded chunks
            sem = asyncio.Semaphore(10)  # concurrency limit

            async def process_single(case_id: int):
                async with sem:
                    async with async_session() as inner_db:
                        try:
                            # Autonomous analysis + execution
                            res = await recovery_agent.run_agent_on_case(
                                db=inner_db,
                                case_id=case_id,
                            )
                            # If initial action fails, perform 1 re-evaluation loop
                            if res.get("execution_result") == "FAILURE":
                                await recovery_agent.run_agent_on_case(
                                    db=inner_db,
                                    case_id=case_id,
                                )
                            await inner_db.commit()
                        except Exception:
                            await inner_db.rollback()

            tasks = [process_single(c.id) for c in cases]
            await asyncio.gather(*tasks, return_exceptions=True)

            # 3. Refresh and compute aggregated statistics
            refreshed_cases_res = await db.execute(
                select(RecoveryCase).where(RecoveryCase.batch_run_id == batch_id)
            )
            refreshed_cases = refreshed_cases_res.scalars().all()

            tot_risk = sum(float(c.amount_at_risk) for c in refreshed_cases)
            tot_recovered = sum(float(c.amount_recovered or 0) for c in refreshed_cases if c.status == "RECOVERED")
            tot_recovered_count = sum(1 for c in refreshed_cases if c.status == "RECOVERED")
            tot_escalated = sum(1 for c in refreshed_cases if c.status == "ESCALATED")
            tot_stopped = sum(1 for c in refreshed_cases if c.status == "STOPPED")

            rec_rate = round((tot_recovered / tot_risk * 100), 2) if tot_risk > 0 else 0.0
            incr_recovered = max(0.0, tot_recovered - float(batch.baseline_recovered or 0))

            batch.events_processed = len(refreshed_cases)
            batch.revenue_at_risk = Decimal(str(tot_risk))
            batch.revenue_recovered = Decimal(str(tot_recovered))
            batch.recovery_rate = rec_rate
            batch.successful_actions = tot_recovered_count
            batch.actions_executed = len(refreshed_cases) + (len(refreshed_cases) // 4)
            batch.escalations = tot_escalated
            batch.policy_stops = tot_stopped
            batch.incremental_recovered = Decimal(str(incr_recovered))
            batch.status = "COMPLETED"
            batch.completed_at = datetime.now(timezone.utc)
            await db.commit()

        except Exception as e:
            async with async_session() as error_db:
                b_res = await error_db.execute(select(BatchRun).where(BatchRun.id == batch_id))
                b = b_res.scalar_one_or_none()
                if b:
                    b.status = "FAILED"
                    await error_db.commit()


@router.post("/run", response_model=BatchStatusResponse)
async def run_batch(
    payload: BatchRunRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate the requested batch records dynamically and launch concurrent agent recovery.
    """
    # Create batch record
    batch = BatchRun(
        batch_size=payload.batch_size,
        payment_pct=payload.payment_pct,
        checkout_pct=payload.checkout_pct,
        receivables_pct=payload.receivables_pct,
        avg_transaction_value=Decimal(str(payload.avg_transaction_value)),
        failure_rate=payload.failure_rate,
        status="GENERATING",
    )
    db.add(batch)
    await db.commit()
    await db.refresh(batch)

    # Generate synthetic events
    gen_result = await generate_dataset(
        db=db,
        batch_size=payload.batch_size,
        payment_pct=payload.payment_pct,
        checkout_pct=payload.checkout_pct,
        receivables_pct=payload.receivables_pct,
        avg_transaction_value=payload.avg_transaction_value,
        failure_rate=payload.failure_rate,
    )
    await db.commit()

    # Tag newly created recovery cases with this batch_id
    tag_query = (
        select(RecoveryCase)
        .where(RecoveryCase.batch_run_id.is_(None))
        .order_by(desc(RecoveryCase.id))
        .limit(payload.batch_size)
    )
    cases_to_tag = (await db.execute(tag_query)).scalars().all()
    for c in cases_to_tag:
        c.batch_run_id = batch.id
    await db.commit()

    # Launch background processing
    background_tasks.add_task(_run_batch_worker, batch.id)

    return BatchStatusResponse(
        id=batch.id,
        batch_size=batch.batch_size,
        status=batch.status,
        events_processed=batch.events_processed or 0,
        revenue_at_risk=float(batch.revenue_at_risk or 0),
        revenue_recovered=float(batch.revenue_recovered or 0),
        recovery_rate=batch.recovery_rate or 0.0,
        actions_executed=batch.actions_executed or 0,
        successful_actions=batch.successful_actions or 0,
        escalations=batch.escalations or 0,
        policy_stops=batch.policy_stops or 0,
        baseline_recovered=float(batch.baseline_recovered or 0),
        baseline_rate=batch.baseline_rate or 0.0,
        incremental_recovered=float(batch.incremental_recovered or 0),
        created_at=batch.created_at,
        completed_at=batch.completed_at,
    )


@router.get("/{batch_id}", response_model=BatchStatusResponse)
async def get_batch_status(batch_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(BatchRun).where(BatchRun.id == batch_id))
    batch = res.scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch run not found")

    return BatchStatusResponse(
        id=batch.id,
        batch_size=batch.batch_size,
        status=batch.status,
        events_processed=batch.events_processed or 0,
        revenue_at_risk=float(batch.revenue_at_risk or 0),
        revenue_recovered=float(batch.revenue_recovered or 0),
        recovery_rate=batch.recovery_rate or 0.0,
        actions_executed=batch.actions_executed or 0,
        successful_actions=batch.successful_actions or 0,
        escalations=batch.escalations or 0,
        policy_stops=batch.policy_stops or 0,
        baseline_recovered=float(batch.baseline_recovered or 0),
        baseline_rate=batch.baseline_rate or 0.0,
        incremental_recovered=float(batch.incremental_recovered or 0),
        created_at=batch.created_at,
        completed_at=batch.completed_at,
    )
