"""
FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from dotenv import load_dotenv
load_dotenv()

from api.routers import ingest, alerts, simulate
from db.mongo_client import connect_db, close_db
import logging
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown events."""
    logger.info("🚀 Starting Threat Detection API...")
    await connect_db()
    yield
    logger.info("🛑 Shutting down Threat Detection API...")
    await close_db()


app = FastAPI(
    title="AI-Driven Threat Detection Engine",
    description="Real-time threat detection, correlation, and explainability for SOC teams.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router, prefix="/ingest", tags=["Ingestion"])
app.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
app.include_router(simulate.router, prefix="/simulate", tags=["Simulation"])


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "threat-detection-api"}
