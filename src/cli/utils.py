"""Shared CLI utilities."""

import sys
from pathlib import Path

import structlog
from rich.console import Console

from coach_config import LegacyPaths
from storage_access import (
    create_insight_store,
    create_intel_storage,
    create_memory_store,
    create_profile_storage,
    create_recommendation_storage,
    create_thread_store,
    create_watchlist_store,
    get_recommendations_dir,
)
from storage_access import (
    get_profile_path as resolve_profile_path,
)
from storage_paths import StoragePaths, get_single_user_paths

console = Console()
logger = structlog.get_logger()


def warn_experimental(feature: str):
    import click

    click.echo(f"[EXPERIMENTAL] {feature} - may change or be removed", err=True)


def get_components(skip_advisor: bool = False):
    """Initialize all components from config.

    Args:
        skip_advisor: If True, skip advisor init (for commands that don't need LLM)
    """
    from advisor import RAGRetriever
    from advisor.engine import AdvisorEngine, APIKeyMissingError
    from cli.config import get_paths, load_config, load_config_model
    from intelligence.embeddings import IntelEmbeddingManager
    from intelligence.search import IntelSearch
    from journal import EmbeddingManager, JournalSearch, JournalStorage
    from journal.fts import JournalFTSIndex

    config = load_config()
    config_model = load_config_model()

    paths = get_paths(config)
    storage_paths = get_storage_paths(config=config, paths=paths)

    storage = JournalStorage(paths["journal_dir"])
    intel_storage = create_intel_storage(storage_paths)

    try:
        embeddings = EmbeddingManager(paths["chroma_dir"])
        intel_embeddings = IntelEmbeddingManager(paths["chroma_dir"] / "intel")
    except Exception as e:
        err = str(e).lower()
        if "dimension" in err or "mismatch" in err:
            console.print(
                "[red]ChromaDB dimension mismatch - embedding model may have changed.[/]\n"
                "Run [bold]coach db rebuild --collection all[/] to fix."
            )
            sys.exit(1)
        raise

    if not embeddings.is_available:
        console.print(
            "[yellow]No embedding provider available — semantic search disabled.[/]\n"
            "Set GOOGLE_API_KEY or OPENAI_API_KEY for semantic search."
        )

    fts_index = JournalFTSIndex(paths["journal_dir"])
    search = JournalSearch(
        storage, embeddings if embeddings.is_available else None, fts_index=fts_index
    )
    intel_search = IntelSearch(
        intel_storage, intel_embeddings if intel_embeddings.is_available else None
    )

    profile_path = get_profile_path(config, storage_paths=storage_paths)
    rag = RAGRetriever(
        search,
        paths["intel_db"],
        intel_search=intel_search,
        max_context_chars=config_model.rag.max_context_chars,
        journal_weight=config_model.rag.journal_weight,
        profile_path=profile_path,
    )

    advisor = None
    if not skip_advisor:
        try:
            llm_cfg = config_model.llm
            advisor = AdvisorEngine(
                rag,
                model=llm_cfg.model,
                provider=llm_cfg.provider,
                api_key=llm_cfg.api_key,
            )
        except APIKeyMissingError as e:
            console.print(f"[red]Config error:[/] {e}")
            sys.exit(1)

    return {
        "config": config,
        "config_model": config_model,
        "paths": paths,
        "storage_paths": storage_paths,
        "storage": storage,
        "embeddings": embeddings,
        "search": search,
        "intel_storage": intel_storage,
        "intel_search": intel_search,
        "rag": rag,
        "advisor": advisor,
    }


def get_storage_paths(
    config: dict | None = None, paths: LegacyPaths | dict | None = None
) -> StoragePaths:
    """Return canonical single-user storage paths for CLI helpers and commands."""
    if config is None:
        from cli.config import load_config

        config = load_config()

    resolved_paths = paths
    if resolved_paths is None:
        raw_intel_db = config.get("paths", {}).get("intel_db", "~/coach/intel.db")
        coach_home = Path(raw_intel_db).expanduser().parent
    else:
        coach_home = Path(resolved_paths["intel_db"]).expanduser().parent

    raw_profile_path = config.get("profile", {}).get("path")
    profile_path = Path(raw_profile_path).expanduser() if raw_profile_path else None
    return get_single_user_paths(coach_home=coach_home, profile_path=profile_path)


def get_rec_db_path(config: dict | None = None, storage_paths: StoragePaths | None = None) -> Path:
    """Get recommendations directory path."""
    resolved_storage_paths = storage_paths or get_storage_paths(config=config)
    return get_recommendations_dir(resolved_storage_paths)


def get_profile_storage(config: dict | None = None, storage_paths: StoragePaths | None = None):
    """Get ProfileStorage instance from config."""
    resolved_storage_paths = storage_paths or get_storage_paths(config=config)
    return create_profile_storage(resolved_storage_paths)


def get_profile_path(config: dict, storage_paths: StoragePaths | None = None) -> str:
    """Get profile YAML path from config."""
    resolved_storage_paths = storage_paths or get_storage_paths(config=config)
    return str(resolve_profile_path(resolved_storage_paths))


def get_thread_store(config: dict | None = None, storage_paths: StoragePaths | None = None):
    """Get the single-user thread store for CLI commands."""
    resolved_storage_paths = storage_paths or get_storage_paths(config=config)
    return create_thread_store(resolved_storage_paths)


def get_watchlist_store(config: dict | None = None, storage_paths: StoragePaths | None = None):
    """Get the single-user watchlist store for CLI commands."""
    resolved_storage_paths = storage_paths or get_storage_paths(config=config)
    return create_watchlist_store(resolved_storage_paths)


def get_memory_store(config: dict | None = None, storage_paths: StoragePaths | None = None):
    """Get the single-user memory store for CLI commands."""
    resolved_storage_paths = storage_paths or get_storage_paths(config=config)
    return create_memory_store(resolved_storage_paths)


def get_intel_storage(config: dict | None = None, storage_paths: StoragePaths | None = None):
    """Get the shared intel store for CLI commands."""
    resolved_storage_paths = storage_paths or get_storage_paths(config=config)
    return create_intel_storage(resolved_storage_paths)


def get_recommendation_storage(
    config: dict | None = None, storage_paths: StoragePaths | None = None
):
    """Get the recommendation store for CLI commands."""
    resolved_storage_paths = storage_paths or get_storage_paths(config=config)
    return create_recommendation_storage(resolved_storage_paths)


def get_insight_store(config: dict | None = None, storage_paths: StoragePaths | None = None):
    """Get the insight store for CLI commands."""
    resolved_storage_paths = storage_paths or get_storage_paths(config=config)
    return create_insight_store(resolved_storage_paths)
