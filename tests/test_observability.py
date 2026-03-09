"""Tests for observability metrics."""

import threading

from observability import Metrics


def test_metrics_counter_is_thread_safe():
    metrics = Metrics()

    def worker():
        for _ in range(1000):
            metrics.counter("hits")

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert metrics.summary()["counters"]["hits"] == 10_000


def test_metrics_token_usage_tracks_cost():
    metrics = Metrics()
    metrics.token_usage("claude-haiku-4-5", 1_000_000, 2_000_000)
    summary = metrics.summary()["token_usage"]["claude-haiku-4-5"]

    assert summary["input_tokens"] == 1_000_000
    assert summary["output_tokens"] == 2_000_000
    assert summary["has_pricing"] is True
    assert summary["estimated_cost_usd"] == 2.75


def test_unknown_model_reports_zero_cost():
    metrics = Metrics()
    metrics.token_usage("mystery-model", 123, 456)
    summary = metrics.summary()["token_usage"]["mystery-model"]

    assert summary["has_pricing"] is False
    assert summary["estimated_cost_usd"] == 0.0
