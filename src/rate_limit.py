"""Token-bucket rate limiter for external API calls."""

import asyncio
import time
from dataclasses import dataclass


@dataclass
class RateLimitConfig:
    """Rate limit parameters."""

    requests_per_second: float = 2.0
    burst: int = 5


class TokenBucketRateLimiter:
    """Async-compatible token bucket rate limiter.

    Allows burst requests up to bucket size, then enforces
    steady-state rate.
    """

    def __init__(self, requests_per_second: float = 2.0, burst: int = 5):
        self.rate = requests_per_second
        self.max_tokens = burst
        self._tokens = float(burst)
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self.max_tokens, self._tokens + elapsed * self.rate)
        self._last_refill = now

    async def acquire(self) -> None:
        """Acquire a token, waiting if necessary."""
        async with self._lock:
            self._refill()
            while self._tokens < 1.0:
                wait_time = (1.0 - self._tokens) / self.rate
                await asyncio.sleep(wait_time)
                self._refill()
            self._tokens -= 1.0

    def acquire_sync(self) -> None:
        """Synchronous version for non-async contexts."""
        self._refill()
        while self._tokens < 1.0:
            wait_time = (1.0 - self._tokens) / self.rate
            time.sleep(wait_time)
            self._refill()
        self._tokens -= 1.0

    @property
    def available_tokens(self) -> float:
        """Current available tokens (for monitoring)."""
        self._refill()
        return self._tokens
