"""Shared configuration loading helpers used across surfaces and domains."""

from pathlib import Path
from typing import Optional, TypedDict

import structlog
import yaml

from cli.config_models import CoachConfig, LimitsConfig

logger = structlog.get_logger()


class LegacyPaths(TypedDict):
    """Legacy 4-key path dictionary returned by get_paths()."""

    journal_dir: Path
    chroma_dir: Path
    intel_db: Path
    log_file: Path


DEFAULTS = LimitsConfig().model_dump()
DEFAULT_CONFIG = CoachConfig().to_dict()


def _deep_merge(base: dict, override: dict) -> dict:
    """Merge validated config values into the original config tree."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def find_config() -> Optional[Path]:
    """Find config file in standard locations."""
    locations = [
        Path.cwd() / "config.yaml",
        Path.home() / ".coach" / "config.yaml",
        Path.home() / "coach" / "config.yaml",
    ]
    for loc in locations:
        if loc.exists():
            return loc
    return None


def load_config(config_path: Optional[Path] = None) -> dict:
    """Load configuration from file or defaults as a dict."""
    path = config_path or find_config()
    base_config = {}

    if path and path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                base_config = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file: {e}")

    validated = load_config_model(path).to_dict()
    return _deep_merge(base_config, validated)


def load_config_model(config_path: Optional[Path] = None) -> CoachConfig:
    """Load configuration as a validated model."""
    base_config = {}

    path = config_path or find_config()
    if path and path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                base_config = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file: {e}")

    try:
        return CoachConfig.from_dict(base_config)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Config validation failed: {e}")


def get_paths(config: dict) -> LegacyPaths:
    """Get expanded paths from config using defaults when unset."""
    paths = config.get("paths", DEFAULT_CONFIG["paths"])
    return LegacyPaths(
        journal_dir=Path(paths.get("journal_dir", "~/coach/journal")).expanduser(),
        chroma_dir=Path(paths.get("chroma_dir", "~/coach/chroma")).expanduser(),
        intel_db=Path(paths.get("intel_db", "~/coach/intel.db")).expanduser(),
        log_file=Path(paths.get("log_file", "~/coach/coach.log")).expanduser(),
    )


def get_limits(config: dict) -> dict:
    """Get limit values, merging user config with defaults."""
    return {**DEFAULTS, **config.get("limits", {})}
