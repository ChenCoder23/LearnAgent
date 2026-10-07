"""第 2 章参考实现。"""

from __future__ import annotations

import inspect
import time
from collections.abc import Callable, Sequence
from functools import partial, reduce, singledispatch, wraps
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])
_MISSING = object()


def make_counter(start: int = 0, step: int = 1) -> Callable[[], int]:
    current = start

    def counter() -> int:
        nonlocal current
        current += step
        return current

    return counter


def make_functions(n: int) -> list[Callable[[], int]]:
    return [partial(_make_one, i) for i in range(n)]


def _make_one(value: int) -> int:
    return value


def compose(*funcs: Callable[[Any], Any]) -> Callable[[Any], Any]:
    if not funcs:
        return lambda value: value

    def composed(value: Any) -> Any:
        return reduce(lambda acc, fn: fn(acc), reversed(funcs), value)

    return composed


def retry(
    func: F | None = None,
    *,
    times: int = 3,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
    delay: float = 0.0,
    backoff: float = 1.0,
) -> Callable[..., Any]:
    if times < 1:
        raise ValueError("times 必须 >= 1")

    def decorator(target: F) -> F:
        @wraps(target)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            wait = delay
            for attempt in range(1, times + 1):
                try:
                    return target(*args, **kwargs)
                except exceptions:
                    if attempt == times:
                        raise  # 直接 re-raise，原始 traceback 与异常类型都不丢
                    if wait:
                        time.sleep(wait)
                        wait *= backoff
            raise AssertionError("不可达：循环必然 return 或 raise")

        return wrapper  # type: ignore[return-value]

    return decorator(func) if func is not None else decorator  # type: ignore[return-value]


def memoize(func: F) -> F:
    cache: dict[Any, Any] = {}
    stats = {"hits": 0, "misses": 0}

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            key = (args, tuple(sorted(kwargs.items())))
            hash(key)
        except TypeError:
            stats["misses"] += 1
            return func(*args, **kwargs)
        if key in cache:
            stats["hits"] += 1
            return cache[key]
        stats["misses"] += 1
        result = func(*args, **kwargs)
        cache[key] = result
        return result

    wrapper.cache_info = lambda: dict(stats)  # type: ignore[attr-defined]
    wrapper.cache_clear = cache.clear  # type: ignore[attr-defined]
    return wrapper  # type: ignore[return-value]


def once(func: F) -> F:
    result: Any = _MISSING

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        nonlocal result
        if result is _MISSING:
            result = func(*args, **kwargs)
        return result

    return wrapper  # type: ignore[return-value]


def timed(func: F) -> F:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        started = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            wrapper.last_elapsed = time.perf_counter() - started  # type: ignore[attr-defined]

    wrapper.last_elapsed = 0.0  # type: ignore[attr-defined]
    return wrapper  # type: ignore[return-value]


@singledispatch
def to_json_like(value: Any) -> str:
    return f"unknown:{type(value).__name__}"


@to_json_like.register(int)
@to_json_like.register(float)
def _(value: Any) -> str:
    return f"number:{value}"


@to_json_like.register(str)
def _(value: str) -> str:
    return f"string:{value}"


@to_json_like.register(list)
@to_json_like.register(tuple)
def _(value: Sequence[Any]) -> str:
    return "array:[" + ",".join(to_json_like(item) for item in value) + "]"


@to_json_like.register(dict)
def _(value: dict[Any, Any]) -> str:
    parts = [f"{key}={to_json_like(value[key])}" for key in sorted(value, key=str)]
    return "object:" + ";".join(parts)


def call_with_kwargs_only(func: Callable[..., Any], **kwargs: Any) -> Any:
    signature = inspect.signature(func)
    accepts_extra = any(
        param.kind is inspect.Parameter.VAR_KEYWORD for param in signature.parameters.values()
    )
    if accepts_extra:
        return func(**kwargs)
    allowed = {name for name in signature.parameters if name in kwargs}
    picked = {name: kwargs[name] for name in allowed}
    return func(**picked)


def pipeline_timer(stages: Sequence[Callable[[Any], Any]], value: Any) -> tuple[Any, float]:
    started = time.perf_counter()
    for stage in stages:
        value = stage(value)
    return value, time.perf_counter() - started
