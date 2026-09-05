"""
RecoverAI — Main FastAPI Application.
Initializes database, seeds initial realistic synthetic dataset,
mounts all API routers, and configures permissive CORS for Vite frontend.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.analytics import router as analytics_router
from app.api.batch import router as batch_router
from app.api.dashboard import router as dashboard_router
from app.api.graph import router as graph_router
from app.api.ledger import router as ledger_router
from app.api.mandates import router as mandates_router
from app.api.policies import router as policies_router
from app.api.promise_to_pay import router as promise_to_pay_router
from app.api.recovery import router as recovery_router
from app.api.revenue_risk import router as revenue_risk_router
from app.api.simulator import router as simulator_router
from app.database.database import async_session, init_db
from app.simulation.data_generator import seed_initial_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database tables and seed initial dataset
    await init_db()
    async with async_session() as db:
        await seed_initial_data(db)
    yield
    # Shutdown logic if needed


app = FastAPI(
    title="RecoverAI — Agentic Revenue Recovery Engine",
    description="Detects revenue risk, diagnoses root causes, and executes bounded recovery interventions.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration for Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all API routers
app.include_router(dashboard_router)
app.include_router(revenue_risk_router)
app.include_router(recovery_router)
app.include_router(batch_router)
app.include_router(ledger_router)
app.include_router(policies_router)
app.include_router(analytics_router)
app.include_router(promise_to_pay_router)
app.include_router(mandates_router)
app.include_router(simulator_router)
app.include_router(graph_router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "app": "RecoverAI", "version": "1.0.0"}
