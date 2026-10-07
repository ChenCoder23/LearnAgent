"""第 6 章参考实现。"""

from __future__ import annotations

import asyncio
import queue
import threading
import time
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from functools import partial, wraps
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def run_serial(delays: Sequence[float]) -> float:
    started = time.perf_counter()
    for delay in delays:
        time.sleep(delay)
    return time.perf_counter() - started


def run_threads(delays: Sequence[float], workers: int = 4) -> float:
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as executor:
        list(executor.map(time.sleep, delays))
    return time.perf_counter() - started


class SafeCounter:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._value = 0

    def increment(self, amount: int = 1) -> None:
        with self._lock:
            self._value += amount

    @property
    def value(self) -> int:
        with self._lock:
            return self._value


def producer_consumer(items: Sequence[int], workers: int = 3) -> int:
    tasks: queue.Queue[int] = queue.Queue()
    for item in items:
        tasks.put(item)
    total = 0
    total_lock = threading.Lock()

    def worker() -> None:
        nonlocal total
        while True:
            try:
                item = tasks.get_nowait()
            except queue.Empty:
                return
            with total_lock:
                total += item

    threads = [threading.Thread(target=worker, name=f"worker-{i}") for i in range(workers)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return total


async def fake_fetch(index: int, delay: float) -> str:
    await asyncio.sleep(delay)
    return f"done-{index}"


async def fetch_all(delays: Sequence[float]) -> list[str]:
    return list(await asyncio.gather(*(fake_fetch(i, d) for i, d in enumerate(delays))))


async def fetch_with_limit(delays: Sequence[float], limit: int) -> tuple[list[str], int]:
    semaphore = asyncio.Semaphore(limit)
    counter_lock = asyncio.Lock()
    current = 0
    peak = 0

    async def one(index: int, delay: float) -> str:
        nonlocal current, peak
        async with semaphore:
            async with counter_lock:
                current += 1
                peak = max(peak, current)
            try:
                await asyncio.sleep(delay)
                return f"done-{index}"
            finally:
                async with counter_lock:
                    current -= 1

    results = await asyncio.gather(*(one(i, d) for i, d in enumerate(delays)))
    return list(results), peak


async def get_or_timeout(delay: float, timeout: float) -> str:
    async def work() -> str:
        await asyncio.sleep(delay)
        return "done"

    return await asyncio.wait_for(work(), timeout=timeout)


async def run_blocking_in_executor(func: Callable[..., Any], *args: Any) -> Any:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, partial(func, *args))


def async_retry(
    times: int = 3,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
    delay: float = 0.0,
    backoff: float = 1.0,
) -> Callable[[F], F]:
    def decorator(target: F) -> F:
        @wraps(target)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            wait = delay
            for attempt in range(1, times + 1):
                try:
                    return await target(*args, **kwargs)
                except exceptions:
                    if attempt == times:
                        raise
                    if wait:
                        await asyncio.sleep(wait)
                        wait *= backoff
            raise AssertionError("不可达")

        return wrapper  # type: ignore[return-value]

    return decorator


async def gather_with_errors(delays: Sequence[float]) -> dict[str, list[Any]]:
    async def maybe(index: int, delay: float) -> str:
        if delay < 0:
            raise ValueError(f"非法延迟: {delay}")
        await asyncio.sleep(delay)
        return f"done-{index}"

    outcomes = await asyncio.gather(
        *(maybe(i, d) for i, d in enumerate(delays)), return_exceptions=True
    )
    ok: list[Any] = []
    errors: list[Any] = []
    for outcome in outcomes:
        if isinstance(outcome, BaseException):
            errors.append(outcome)
        else:
            ok.append(outcome)
    return {"ok": ok, "errors": errors}
