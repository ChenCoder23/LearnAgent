"""第 9 章参考实现。"""

from __future__ import annotations

import json
import random
import threading
import time
import uuid
from collections.abc import Callable
from typing import Any

NULL_SENTINEL = "__NULL__"


class MemoryStore:
    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._data: dict[str, tuple[str, float | None]] = {}
        # 真实 Redis 的单条命令是原子的；这里用一把锁模拟，否则 NX 会出现竞态
        self._lock = threading.Lock()

    def _alive(self, key: str) -> tuple[str, float | None] | None:
        item = self._data.get(key)
        if item is None:
            return None
        _, expire_at = item
        if expire_at is not None and expire_at <= self._clock():
            del self._data[key]
            return None
        return item

    def set(self, key: str, value: str, *, nx: bool = False, ex: float | None = None) -> bool:
        with self._lock:
            if nx and self._alive(key) is not None:
                return False
            expire_at = None if ex is None else self._clock() + ex
            self._data[key] = (value, expire_at)
            return True

    def get(self, key: str) -> str | None:
        item = self._alive(key)
        return item[0] if item is not None else None

    def delete(self, *keys: str) -> int:
        removed = 0
        for key in keys:
            if self._alive(key) is not None:
                del self._data[key]
                removed += 1
        return removed

    def exists(self, key: str) -> bool:
        return self._alive(key) is not None

    def incr(self, key: str) -> int:
        with self._lock:
            item = self._alive(key)
            current = int(item[0]) + 1 if item is not None else 1
            expire_at = item[1] if item is not None else None
            self._data[key] = (str(current), expire_at)
            return current

    def ttl(self, key: str) -> float | None:
        item = self._alive(key)
        if item is None or item[1] is None:
            return None
        return max(0.0, item[1] - self._clock())

    def delete_if_value(self, key: str, value: str) -> bool:
        with self._lock:
            item = self._alive(key)
            if item is None or item[0] != value:
                return False
            del self._data[key]
            return True


def cache_key(*parts: Any) -> str:
    cleaned = [str(part) for part in parts if part is not None and str(part) != ""]
    return ":".join(cleaned)


def serialize(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def deserialize(raw: str) -> Any:
    if raw == NULL_SENTINEL:
        return None
    return json.loads(raw)


def get_or_load(
    store: MemoryStore, key: str, loader: Callable[[], Any], ttl: float | None = None
) -> tuple[Any, bool]:
    cached = store.get(key)
    if cached is not None:
        return deserialize(cached), True
    value = loader()
    store.set(key, serialize(value), ex=ttl)
    return value, False


def get_or_load_with_null(
    store: MemoryStore,
    key: str,
    loader: Callable[[], Any],
    ttl: float = 60,
    null_ttl: float = 10,
) -> tuple[Any, bool]:
    cached = store.get(key)
    if cached is not None:
        return deserialize(cached), True
    value = loader()
    if value is None:
        store.set(key, NULL_SENTINEL, ex=null_ttl)
        return None, False
    store.set(key, serialize(value), ex=ttl)
    return value, False


def single_flight(
    store: MemoryStore,
    key: str,
    loader: Callable[[], Any],
    ttl: float = 60,
    *,
    lock_ttl: float = 5,
    wait: float = 0.01,
    retries: int = 50,
) -> Any:
    cached = store.get(key)
    if cached is not None:
        return deserialize(cached)

    lock = DistributedLock(store, f"lock:{key}", ttl=lock_ttl)
    if lock.acquire():
        try:
            cached = store.get(key)  # 双检：可能在抢锁期间别人已经写好
            if cached is not None:
                return deserialize(cached)
            value = loader()
            store.set(key, serialize(value), ex=ttl)
            return value
        finally:
            lock.release()

    for _ in range(retries):
        time.sleep(wait)
        cached = store.get(key)
        if cached is not None:
            return deserialize(cached)

    value = loader()  # 兜底：宁可多查一次，也不要让请求失败
    store.set(key, serialize(value), ex=ttl)
    return value


def jittered_ttl(base: float, ratio: float = 0.2) -> float:
    low = base * (1 - ratio)
    high = base * (1 + ratio)
    return random.uniform(low, high)


class DistributedLock:
    def __init__(
        self, store: MemoryStore, key: str, ttl: float = 5, token: str | None = None
    ) -> None:
        self.store = store
        self.key = key
        self.ttl = ttl
        self.token = token or uuid.uuid4().hex
        self.acquired = False

    def acquire(self) -> bool:
        self.acquired = self.store.set(self.key, self.token, nx=True, ex=self.ttl)
        return self.acquired

    def release(self) -> bool:
        if not self.acquired:
            return False
        released = self.store.delete_if_value(self.key, self.token)
        self.acquired = False
        return released

    def __enter__(self) -> DistributedLock:
        if not self.acquire():
            raise RuntimeError(f"获取锁失败: {self.key}")
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.release()


def redis_release_lua() -> str:
    return """
if redis.call('get', KEYS[1]) == ARGV[1] then
    return redis.call('del', KEYS[1])
else
    return 0
end
""".strip()


def idempotent(
    store: MemoryStore, key: str, action: Callable[[], Any], ttl: float = 3600
) -> tuple[str, Any]:
    cached = store.get(key)
    if cached is not None:
        return "replayed", deserialize(cached)
    result = action()
    store.set(key, serialize(result), ex=ttl)
    return "executed", result


def rate_limit(store: MemoryStore, key: str, limit: int, window: float) -> tuple[bool, int]:
    count = store.incr(key)
    if count == 1:
        store.set(key, str(count), ex=window)
    return count <= limit, count
