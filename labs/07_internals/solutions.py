"""第 7 章参考实现。"""

from __future__ import annotations

import copy
import dis
import gc
import sys
import timeit
import types
import weakref
from collections.abc import Callable
from typing import Any


def int_interning() -> tuple[bool, bool]:
    small_a = 256
    small_b = 256
    big_a = int("1000")
    big_b = int("1000")
    return small_a is small_b, big_a is big_b


def string_interning() -> tuple[bool, bool]:
    literal_a = "hello"
    literal_b = "hello"
    literal = "hello"
    built = "".join(["h", "e", "l", "l", "o"])
    return literal_a is literal_b, built is literal


def refcount_grows() -> tuple[int, int]:
    payload = object()
    base = sys.getrefcount(payload)
    holder = [payload]
    with_extra = sys.getrefcount(payload)
    assert holder  # 防止被优化掉
    return base, with_extra


def cycle_is_collected() -> tuple[bool, bool]:
    class Node:
        pass

    gc.collect()  # 先清一次，避免把之前残留的垃圾算进来
    first = Node()
    second = Node()
    first.peer = second
    second.peer = first
    tracked = gc.is_tracked(first)
    del first, second
    collected = gc.collect()
    return collected > 0, tracked


def mutable_default_trap() -> Callable[[str], list[str]]:
    def append_item(item: str, acc: list[str] = []) -> list[str]:  # noqa: B006 - 故意演示坑
        acc.append(item)
        return acc

    return append_item


def mutable_default_fixed() -> Callable[[str], list[str]]:
    def append_item(item: str, acc: list[str] | None = None) -> list[str]:
        bucket = list(acc) if acc is not None else []
        bucket.append(item)
        return bucket

    return append_item


def bytecode_ops(func: Callable[..., Any], recursive: bool = False) -> list[str]:
    ops: list[str] = []
    for instruction in dis.get_instructions(func):
        ops.append(instruction.opname)
        if recursive and isinstance(instruction.argval, types.CodeType):
            ops.extend(bytecode_ops(instruction.argval, recursive=True))
    return ops


class LazyConfig:
    def __init__(self, source: dict[str, str]) -> None:
        object.__setattr__(self, "_source", source)
        object.__setattr__(self, "cache", {})
        object.__setattr__(self, "loads", 0)

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        cache = object.__getattribute__(self, "cache")
        if name in cache:
            return cache[name]
        source = object.__getattribute__(self, "_source")
        if name not in source:
            raise AttributeError(name)
        value = {"region": "cn", name: source[name].upper()}
        cache[name] = value
        object.__setattr__(self, "loads", object.__getattribute__(self, "loads") + 1)
        return value


def copy_semantics() -> tuple[list[Any], list[Any], list[Any]]:
    original: list[Any] = [[1], 2]
    shallow = copy.copy(original)
    deep = copy.deepcopy(original)
    shallow[0].append(9)
    deep[0].append(8)
    return original, shallow, deep


class Big:
    def __init__(self, name: str) -> None:
        self.name = name


def weak_cache_roundtrip() -> tuple[int, int]:
    cache: weakref.WeakValueDictionary[str, Big] = weakref.WeakValueDictionary()
    item = Big("temp")
    cache["a"] = item
    size_with_strong_ref = len(cache)
    del item
    gc.collect()
    return size_with_strong_ref, len(cache)


def benchmark(func: Callable[[], Any], number: int = 1000) -> float:
    return timeit.timeit(func, number=number)
