"""Configuration loading and management."""

from pathlib import Path
from typing import Optional

import structlog

from coach_config import LegacyPaths
from coach_config import get_paths as _get_paths
from coach_config import load_config as _load_config
from coach_config import load_config_model as _load_config_model

from .config_models import CoachConfig, LimitsConfig

logger = structlog.get_logger()


# Default values for tunable parameters (backwards compat)
DEFAULTS = LimitsConfig().model_dump()

# Default config dict (backwards compat)
DEFAULT_CONFIG = CoachConfig().to_dict()


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
    """Load configuration from file or defaults.

    Returns dict for backwards compatibility. Use load_config_model() for typed access.
    """
    return _load_config(config_path)


def load_config_model(config_path: Optional[Path] = None) -> CoachConfig:
    """Load configuration as Pydantic model with validation."""
    return _load_config_model(config_path)


def _deep_merge(base: dict, override: dict) -> dict:
    """Deep merge two dictionaries."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def get_paths(config: dict) -> LegacyPaths:
    """Get expanded paths from config."""
    return _get_paths(config)


def get_limits(config: dict) -> dict:
    """Get limit values, merging user config with defaults."""
    return {**DEFAULTS, **config.get("limits", {})}


def setup_logging(config: dict) -> None:
    """Configure logging based on config."""
    from cli.logging_config import setup_logging as _setup

    log_config = config.get("logging", {})
    level = log_config.get("level", "INFO")
    json_mode = log_config.get("json_mode", False)
    _setup(json_mode=json_mode, level=level)
