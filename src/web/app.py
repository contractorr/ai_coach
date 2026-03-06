"""FastAPI application entry point."""

import os
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from web.routes import (
    admin,
    advisor,
    briefing,
    engagement,
    goals,
    greeting,
    heartbeat,
    intel,
    journal,
    learning,
    memory,
    onboarding,
    pageview,
    predictions,
    profile,
    recommendations,
    research,
    settings,
    threads,
    user,
)
from web.user_store import init_db

logger = structlog.get_logger()


def _verify_secret_key() -> None:
    """Canary check: encrypt+decrypt roundtrip with SECRET_KEY on startup."""
    key = os.getenv("SECRET_KEY")
    if not key:
        logger.critical("SECRET_KEY env var not set")
        raise RuntimeError("SECRET_KEY required")
    from web.crypto import decrypt_value, encrypt_value

    canary = "canary-check"
    enc = encrypt_value(key, canary)
    dec = decrypt_value(key, enc, key_name="canary")
    if dec != canary:
        logger.critical("SECRET_KEY canary failed — key may have changed")
        raise RuntimeError("SECRET_KEY canary failed")
    logger.info("crypto.canary_ok")


def _start_intel_scheduler():
    """Start background intel scheduler (daily 6am scrape)."""
    try:
        from intelligence.scheduler import IntelScheduler
        from web.deps import get_coach_paths, get_config

        config = get_config()
        full = config.to_dict()
        paths = get_coach_paths()

        from intelligence.scraper import IntelStorage

        storage = IntelStorage(paths["intel_db"])

        scheduler = IntelScheduler(
            storage=storage,
            config=full.get("sources", {}),
            full_config=full,
        )
        cron = full.get("schedule", {}).get("intelligence_gather", "0 6 * * *")
        scheduler.start(cron_expr=cron)
        logger.info("intel_scheduler.started", cron=cron)
        return scheduler
    except Exception as e:
        logger.error("intel_scheduler.start_failed", error=str(e))
        return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    _verify_secret_key()
    scheduler = _start_intel_scheduler()
    logger.info("web.startup")
    yield
    if scheduler:
        scheduler.stop()
    logger.info("web.shutdown")


app = FastAPI(
    title="AI Coach",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow frontend origin
frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes
app.include_router(settings.router)
app.include_router(journal.router)
app.include_router(advisor.router)
app.include_router(goals.router)
app.include_router(intel.router)
app.include_router(research.router)
app.include_router(onboarding.router)
app.include_router(briefing.router)
app.include_router(greeting.router)
app.include_router(recommendations.router)
app.include_router(engagement.router)
app.include_router(profile.router)
app.include_router(user.router)
app.include_router(pageview.router)
app.include_router(learning.router)
app.include_router(admin.router)
app.include_router(heartbeat.router)
app.include_router(memory.router)
app.include_router(threads.router)
app.include_router(predictions.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
