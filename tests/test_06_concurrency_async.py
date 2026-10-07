"""第 6 章测试：线程、队列、asyncio 限流与重试。"""

from __future__ import annotations

import asyncio
import threading
import time

import pytest

from learnkit import load

m = load("06_concurrency_async")


def test_threads_beat_serial_for_io_bound_work():
    delays = [0.05] * 4
    serial = m.run_serial(delays)
    threaded = m.run_threads(delays, workers=4)
    assert serial >= 0.19
    assert threaded < serial * 0.8, f"线程池应该更快: serial={serial:.3f} threaded={threaded:.3f}"


def test_safe_counter_under_contention():
    counter = m.SafeCounter()
    threads = [threading.Thread(target=lambda: [counter.increment() for _ in range(200)]) for _ in range(20)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert counter.value == 4000


def test_producer_consumer_sums_everything():
    assert m.producer_consumer(list(range(100))) == 4950
    assert m.producer_consumer([], workers=2) == 0


def test_fetch_all_is_concurrent_and_ordered():
    delays = [0.05, 0.05, 0.05, 0.05]
    started = time.perf_counter()
    results = asyncio.run(m.fetch_all(delays))
    elapsed = time.perf_counter() - started
    assert results == ["done-0", "done-1", "done-2", "done-3"]
    assert elapsed < 0.15, "gather 应该是并发执行，而不是排队"


def test_fetch_with_limit_caps_concurrency():
    results, peak = asyncio.run(m.fetch_with_limit([0.03] * 6, limit=2))
    assert len(results) == 6
    assert peak == 2, f"并发峰值应等于 limit，实际 {peak}"


def test_timeout_and_blocking_bridge():
    assert asyncio.run(m.get_or_timeout(0.01, timeout=0.5)) == "done"
    with pytest.raises(TimeoutError):
        asyncio.run(m.get_or_timeout(0.3, timeout=0.02))
    assert asyncio.run(m.run_blocking_in_executor(lambda x: x * 2, 21)) == 42


def test_async_retry():
    state = {"calls": 0}

    @m.async_retry(times=3, delay=0)
    async def flaky() -> str:
        state["calls"] += 1
        if state["calls"] < 3:
            raise RuntimeError("还没成功")
        return "ok"

    assert asyncio.run(flaky()) == "ok"
    assert state["calls"] == 3

    @m.async_retry(times=2, delay=0)
    async def always_fail() -> None:
        raise RuntimeError("一直失败")

    with pytest.raises(RuntimeError):
        asyncio.run(always_fail())


def test_gather_with_errors_isolates_failures():
    outcome = asyncio.run(m.gather_with_errors([0.01, -1, 0.01]))
    assert outcome["ok"] == ["done-0", "done-2"]
    assert len(outcome["errors"]) == 1
    assert isinstance(outcome["errors"][0], ValueError)
