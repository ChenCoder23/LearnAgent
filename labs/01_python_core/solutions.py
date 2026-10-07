"""第 1 章参考实现。卡住 30 分钟以上再看，看完必须合上重写。"""

from __future__ import annotations

import copy
from collections import defaultdict
from collections.abc import Callable, Iterable, Sequence
from typing import Any

_ZERO_WIDTH = "\u200b\u200c\u200d\ufeff"


def dedupe(seq: Iterable[Any]) -> list[Any]:
    seen: set[Any] = set()
    result: list[Any] = []
    for item in seq:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def parse_version(text: str) -> dict[str, Any]:
    raw = text
    if not isinstance(text, str) or not text:
        raise ValueError(f"非法版本号: {raw!r}")

    pre: str | None = None
    build: str | None = None
    body = text
    if "+" in body:
        body, _, build = body.partition("+")
        if not build:
            raise ValueError(f"非法版本号: {raw!r}")
    if "-" in body:
        body, _, pre = body.partition("-")
        if not pre:
            raise ValueError(f"非法版本号: {raw!r}")

    parts = body.split(".")
    if len(parts) != 3:
        raise ValueError(f"非法版本号: {raw!r}")
    numbers: list[int] = []
    for part in parts:
        if not part.isdigit():
            raise ValueError(f"非法版本号: {raw!r}")
        numbers.append(int(part))
    return {
        "major": numbers[0],
        "minor": numbers[1],
        "patch": numbers[2],
        "pre": pre,
        "build": build,
    }


def group_by(items: Iterable[Any], key: str | Callable[[Any], Any]) -> dict[Any, list[Any]]:
    key_func: Callable[[Any], Any] = key if callable(key) else (lambda item: item[key])
    grouped: dict[Any, list[Any]] = defaultdict(list)
    for item in items:
        grouped[key_func(item)].append(item)
    return dict(grouped)


def flatten(nested: Iterable[Any], *, skip_none: bool = True) -> list[Any]:
    result: list[Any] = []
    stack: list[Any] = [nested]
    while stack:
        current = stack.pop()
        if isinstance(current, (list, tuple)):
            stack.extend(reversed(current))
            continue
        if current is None and skip_none:
            continue
        result.append(current)
    return result


def chunk(seq: Sequence[Any], size: int) -> list[list[Any]]:
    if size <= 0:
        raise ValueError("size 必须大于 0")
    return [list(seq[i : i + size]) for i in range(0, len(seq), size)]


def deep_get(data: Any, path: str, default: Any = None) -> Any:
    current = data
    for segment in path.split("."):
        if isinstance(current, dict):
            if segment not in current:
                return default
            current = current[segment]
        elif isinstance(current, (list, tuple)):
            if not segment.isdigit():
                return default
            index = int(segment)
            if index >= len(current):
                return default
            current = current[index]
        else:
            return default
    return current


def normalize(text: str) -> str:
    cleaned = text
    for ch in _ZERO_WIDTH:
        cleaned = cleaned.replace(ch, "")
    return " ".join(cleaned.split())


def summarize(nums: Sequence[float]) -> dict[str, float]:
    if not nums:
        raise ValueError("nums 不能为空")
    ordered = sorted(nums)
    n = len(ordered)
    if n % 2:
        median = float(ordered[n // 2])
    else:
        median = (ordered[n // 2 - 1] + ordered[n // 2]) / 2
    return {
        "min": float(ordered[0]),
        "max": float(ordered[-1]),
        "mean": sum(ordered) / n,
        "median": float(median),
    }


def add_tag(tag: str, tags: list[str] | None = None) -> list[str]:
    new_tags = list(tags) if tags is not None else []
    new_tags.append(tag)
    return new_tags


def merge_config(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_config(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged
