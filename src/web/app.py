"""FastAPI application entry point."""

import os
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from crypto_utils import decrypt_value, encrypt_value
from user_state_store import init_db
from web.routes import ROUTERS

logger = structlog.get_logger()


def _env_flag(name: str, default: bool = False) -> bool:
    """Parse a boolean env flag with a conservative default."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _verify_secret_key() -> None:
    """Canary check: encrypt+decrypt roundtrip with SECRET_KEY on startup."""
    key = os.getenv("SECRET_KEY")
    if not key:
        logger.critical("SECRET_KEY env var not set")
        raise RuntimeError("SECRET_KEY required")
    canary = "canary-check"
    enc = encrypt_value(key, canary)
    dec = decrypt_value(key, enc, key_name="canary")
    if dec != canary:
        logger.critical("SECRET_KEY canary failed — key may have changed")
        raise RuntimeError("SECRET_KEY canary failed")
    logger.info("crypto.canary_ok")


def _build_web_user_contexts(require_personal_key: bool = False) -> list[dict]:
    from journal.embeddings import EmbeddingManager
    from journal.storage import JournalStorage
    from web.deps import get_personal_llm_keys_for_user, get_user_paths, safe_user_id
    from web.user_store import list_user_ids

    contexts = []
    for user_id in list_user_ids():
        if require_personal_key and not get_personal_llm_keys_for_user(user_id):
            continue
        paths = get_user_paths(user_id)
        contexts.append(
            {
                "user_id": user_id,
                "paths": paths,
                "journal_storage": JournalStorage(paths["journal_dir"]),
                "embeddings": EmbeddingManager(
                    paths["chroma_dir"],
                    collection_name=f"journal_{safe_user_id(user_id)}",
                ),
            }
        )
    return contexts


def _run_web_research_for_user(user_id: str):
    from web.routes.research import _get_agent

    agent = _get_agent(user_id)
    try:
        return agent.run()
    finally:
        try:
            agent.close()
        except Exception:
            pass


def _run_web_recommendations_for_user(user_id: str) -> dict:
    from journal.storage import JournalStorage
    from web.deps import get_config, get_user_paths
    from web.routes.advisor import _get_engine

    config = get_config().to_dict()
    rec_config = config.get("recommendations", {})
    delivery = rec_config.get("delivery", {})
    max_per_cat = rec_config.get("scoring", {}).get("max_per_category", 3)
    paths = get_user_paths(user_id)

    advisor = _get_engine(user_id, use_tools=False)
    recs = advisor.generate_recommendations(
        "all",
        paths["recommendations_dir"],
        rec_config,
        max_items=max_per_cat,
    )

    brief_saved = False
    if "journal" in delivery.get("methods", ["journal"]):
        advisor.generate_action_brief(
            paths["recommendations_dir"],
            journal_storage=JournalStorage(paths["journal_dir"]),
            save=True,
        )
        brief_saved = True

    return {"recommendations": len(recs), "brief_saved": brief_saved}


def _start_intel_scheduler():
    """Start background intel scheduler (daily 6am scrape)."""
    if _env_flag("DISABLE_INTEL_SCHEDULER"):
        logger.info("intel_scheduler.disabled")
        return None

    try:
        from intelligence.scheduler import IntelScheduler
        from web.deps import get_config, get_intel_storage

        config = get_config()
        full = config.to_dict()
        storage = get_intel_storage()

        scheduler = IntelScheduler(
            storage=storage,
            config=full.get("sources", {}),
            full_config=full,
            web_user_contexts_factory=_build_web_user_contexts,
            web_research_runner=_run_web_research_for_user,
            web_recommendations_runner=_run_web_recommendations_for_user,
        )
        cron = full.get("schedule", {}).get("intelligence_gather", "0 6 * * *")
        scheduler.start_web(cron_expr=cron)
        logger.info("intel_scheduler.started", cron=cron)
        return scheduler
    except Exception as e:
        logger.error("intel_scheduler.start_failed", error=str(e))
        return None


def _startup_services():
    """Initialize process-level web services and return shutdown state."""
    init_db()
    _verify_secret_key()
    scheduler = _start_intel_scheduler()
    logger.info("web.startup")
    return {"scheduler": scheduler}


def _shutdown_services(state: dict | None) -> None:
    """Stop process-level web services started during lifespan."""
    scheduler = (state or {}).get("scheduler")
    if scheduler:
        scheduler.stop()
    logger.info("web.shutdown")


@asynccontextmanager
async def lifespan(app: FastAPI):
    state = _startup_services()
    yield
    _shutdown_services(state)


async def health():
    return {"status": "ok"}


def _configure_cors(app: FastAPI) -> None:
    """Attach CORS middleware using env-driven frontend origin."""
    frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def _register_routes(app: FastAPI) -> None:
    """Mount all API routers and health check."""
    for router in ROUTERS:
        app.include_router(router)
    app.add_api_route("/api/health", health, methods=["GET"])


def create_app() -> FastAPI:
    """Create the FastAPI application with middleware and routes."""
    app = FastAPI(
        title="AI Coach",
        version="0.1.0",
        lifespan=lifespan,
    )
    _configure_cors(app)
    _register_routes(app)
    return app


app = create_app()
