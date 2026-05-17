# backend/main.py
# FastAPI application entry point.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.database import engine, Base
from backend.routers import resume, jobs, outputs
from backend.utils.logger import get_logger
from backend.utils.redis_cache import check_redis_health
from backend.config import settings

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    logger.info(f"Starting JobPilot API — env={settings.app_env}")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")

    redis_ok = await check_redis_health()
    if redis_ok:
        logger.info("Redis connection OK")
    else:
        logger.warning("Redis unavailable — caching disabled, app will still work")

    yield

    # Shutdown
    logger.info("JobPilot API shutting down")


app = FastAPI(
    title="JobPilot API",
    description="AI-powered job application optimizer",
    version="1.0.0",
    lifespan=lifespan
)

# CORS — allow Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],         # tighten to specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(resume.router,  prefix="/resume",  tags=["Resume"])
app.include_router(jobs.router,    prefix="/jobs",    tags=["Jobs"])
app.include_router(outputs.router, prefix="/outputs", tags=["Outputs"])


@app.get("/health", tags=["Health"])
async def health():
    """Health check — used by Docker, Render, Railway."""
    redis_ok = await check_redis_health()
    return {
        "status": "ok",
        "version": "1.0.0",
        "env": settings.app_env,
        "redis": "connected" if redis_ok else "unavailable",
        "model": settings.ollama_model
    }
