"""第 4 章参考实现。"""

from __future__ import annotations

import time
from collections import deque
from collections.abc import Generator, Iterable, Iterator
from contextlib import contextmanager, suppress
from typing import Any


class Countdown:
    def __init__(self, start: int) -> None:
        self.current = start

    def __iter__(self) -> Iterator[int]:
        return self

    def __next__(self) -> int:
        if self.current <= 0:
            raise StopIteration
        value = self.current
        self.current -= 1
        return value


def take(n: int, iterable: Iterable[Any]) -> list[Any]:
    result: list[Any] = []
    for item in iterable:
        if len(result) >= n:
            break
        result.append(item)
    return result


def sliding_window(iterable: Iterable[Any], k: int) -> Iterator[tuple[Any, ...]]:
    if k <= 0:
        raise ValueError("k 必须大于 0")
    window: deque[Any] = deque(maxlen=k)
    for item in iterable:
        window.append(item)
        if len(window) == k:
            yield tuple(window)


def read_in_batches(lines: Iterable[str], size: int) -> Iterator[list[str]]:
    if size <= 0:
        raise ValueError("size 必须大于 0")
    batch: list[str] = []
    for line in lines:
        batch.append(line)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch


def pipe(data: Iterable[Any], *stages: Any) -> Iterator[Any]:
    current: Iterable[Any] = data
    for stage in stages:
        current = stage(current)
    yield from current


class Timer:
    def __enter__(self) -> Timer:
        self.started = time.perf_counter()
        self.elapsed = 0.0
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.elapsed = time.perf_counter() - self.started
        return None  # 不吞异常


@contextmanager
def transaction(store: dict[str, Any]) -> Generator[dict[str, Any], None, None]:
    snapshot = dict(store)
    try:
        yield store
    except Exception:
        store.clear()
        store.update(snapshot)
        raise


class AppError(Exception):
    pass


class NotFoundError(AppError):
    pass


class ValidationError(AppError):
    pass


def load_user(store: dict[str, dict[str, Any]], user_id: str) -> dict[str, Any]:
    try:
        user = store[user_id]
    except KeyError as error:
        raise NotFoundError(f"用户不存在: {user_id}") from error
    if "name" not in user:
        raise ValidationError(f"用户数据缺少 name 字段: {user_id}")
    return user


def parse_int(text: str, default: int = 0) -> int:
    with suppress(ValueError):
        return int(text)
    return default


def trace_order(fail: bool) -> list[str]:
    events: list[str] = []
    try:
        events.append("try")
        if fail:
            raise ValueError("boom")
    except ValueError:
        events.append("except")
    else:
        events.append("else")
    finally:
        events.append("finally")
    return events


def safe_divide(a: float, b: float) -> float:
    if b == 0:
        raise ValidationError("除数不能为 0")
    return a / b


def running_average() -> Generator[float | None, float, None]:
    total = 0.0
    count = 0
    average: float | None = None
    while True:
        value = yield average
        total += value
        count += 1
        average = total / count
