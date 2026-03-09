"""Retry utilities with exponential backoff."""

import logging

import structlog
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = structlog.stdlib.get_logger(__name__)


def http_retry(
    max_attempts: int = 3,
    min_wait: float = 2.0,
    max_wait: float = 10.0,
    exceptions: tuple = (Exception,),
):
    """Retry decorator for HTTP/scraper operations.

    Args:
        max_attempts: Max retry attempts
        min_wait: Min wait between retries (seconds)
        max_wait: Max wait between retries (seconds)
        exceptions: Exception types to retry on
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(exceptions),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )


def llm_retry(
    max_attempts: int = 3,
    min_wait: float = 2.0,
    max_wait: float = 30.0,
    exceptions: tuple = (Exception,),
):
    """Retry decorator for LLM API calls.

    Uses longer max_wait for rate limiting scenarios.

    Args:
        max_attempts: Max retry attempts
        min_wait: Min wait between retries (seconds)
        max_wait: Max wait between retries (seconds)
        exceptions: Exception types to retry on
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(exceptions),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )


def with_retry(
    max_attempts: int = 3,
    min_wait: float = 2.0,
    max_wait: float = 10.0,
    exceptions: tuple = (Exception,),
):
    """Generic retry decorator.

    Args:
        max_attempts: Max retry attempts
        min_wait: Min wait between retries (seconds)
        max_wait: Max wait between retries (seconds)
        exceptions: Exception types to retry on
    """
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(exceptions),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )


def retry_from_config(config: dict, retry_type: str = "http"):
    """Create retry decorator from config dict.

    Args:
        config: Config dict with retry section
        retry_type: "http" or "llm"

    Returns:
        Configured retry decorator
    """
    retry_config = config.get("retry", {})

    max_attempts = retry_config.get("max_attempts", 3)
    min_wait = retry_config.get("min_wait", 2.0)

    if retry_type == "llm":
        max_wait = retry_config.get("llm_max_wait", 30.0)
    else:
        max_wait = retry_config.get("max_wait", 10.0)

    return with_retry(
        max_attempts=max_attempts,
        min_wait=min_wait,
        max_wait=max_wait,
    )
