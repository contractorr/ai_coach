"""Per-user rate limiting for shared-key (lite mode) users.

In-memory sliding window — resets on deploy. Acceptable for now.
"""

import time
from collections import defaultdict

from fastapi import HTTPException

# 30 queries per rolling 24h window
DAILY_LIMIT = 30
WINDOW_SECONDS = 86400  # 24h

# Burst: 1 request per 10 seconds
BURST_INTERVAL = 10.0

# Onboarding gets a separate, more generous budget so users can finish
# the profile interview without exhausting their daily allowance.
ONBOARDING_BURST_INTERVAL = 3.0
ONBOARDING_LIMIT = 20  # max turns in one onboarding session

# user_id -> list of timestamps
_request_log: dict[str, list[float]] = defaultdict(list)
_onboarding_log: dict[str, list[float]] = defaultdict(list)


def _prune(user_id: str, now: float) -> list[float]:
    """Remove timestamps older than the window."""
    cutoff = now - WINDOW_SECONDS
    log = [t for t in _request_log[user_id] if t > cutoff]
    _request_log[user_id] = log
    return log


def check_shared_key_rate_limit(user_id: str, *, onboarding: bool = False) -> None:
    """Raise 429 if shared-key user exceeds limits.

    Onboarding calls use a separate budget so the profile interview
    never competes with regular usage.
    """
    now = time.time()

    if onboarding:
        _check_onboarding_limit(user_id, now)
        return

    log = _prune(user_id, now)

    # Burst check
    if log and (now - log[-1]) < BURST_INTERVAL:
        retry_after = int(BURST_INTERVAL - (now - log[-1])) + 1
        raise HTTPException(
            status_code=429,
            detail="Lite mode limit reached — add your own API key in Settings for unlimited access",
            headers={"Retry-After": str(retry_after)},
        )

    # Daily limit check
    if len(log) >= DAILY_LIMIT:
        oldest = log[0]
        retry_after = int(oldest + WINDOW_SECONDS - now) + 1
        raise HTTPException(
            status_code=429,
            detail="Lite mode limit reached — add your own API key in Settings for unlimited access",
            headers={"Retry-After": str(retry_after)},
        )

    # Record request
    _request_log[user_id].append(now)


def _check_onboarding_limit(user_id: str, now: float) -> None:
    """Separate rate limit for onboarding — generous burst, capped per session."""
    cutoff = now - 3600  # 1h window for onboarding
    log = [t for t in _onboarding_log[user_id] if t > cutoff]
    _onboarding_log[user_id] = log

    if log and (now - log[-1]) < ONBOARDING_BURST_INTERVAL:
        retry_after = int(ONBOARDING_BURST_INTERVAL - (now - log[-1])) + 1
        raise HTTPException(
            status_code=429,
            detail="Please wait a moment before sending the next message",
            headers={"Retry-After": str(retry_after)},
        )

    if len(log) >= ONBOARDING_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="Onboarding session limit reached — please try again later or add your own API key in Settings",
            headers={"Retry-After": "60"},
        )

    _onboarding_log[user_id].append(now)


def reset_rate_limits() -> None:
    """Clear all rate limit state. Used in tests."""
    _request_log.clear()
