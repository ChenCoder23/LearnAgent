"""第 9 章测试：缓存三大问题、分布式锁、幂等、限流。"""

from __future__ import annotations

import threading
import time

from learnkit import load

m = load("09_cache_redis")


class FakeClock:
    """假时钟：推进时间不用真的 sleep。"""

    def __init__(self, now: float = 0.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def test_store_set_nx_ttl_and_expiry():
    clock = FakeClock()
    store = m.MemoryStore(clock=clock)
    assert store.set("a", "1", ex=5) is True
    assert store.get("a") == "1"
    assert store.ttl("a") == 5
    assert store.set("a", "2", nx=True) is False, "NX 在 key 存在时必须失败"
    assert store.get("a") == "1"
    clock.advance(5.1)
    assert store.get("a") is None, "过期后读不到"
    assert store.exists("a") is False
    assert store.ttl("missing") is None


def test_store_incr_keeps_ttl_and_delete_if_value():
    clock = FakeClock()
    store = m.MemoryStore(clock=clock)
    store.set("counter", "0", ex=10)
    assert store.incr("counter") == 1
    assert store.incr("counter") == 2
    assert store.ttl("counter") == 10, "INCR 不能重置 TTL"
    assert store.incr("fresh") == 1
    assert store.delete_if_value("counter", "wrong") is False
    assert store.delete_if_value("counter", "2") is True
    assert store.delete("fresh", "missing") == 1


def test_cache_key_normalization():
    assert m.cache_key("article", 42, None, "detail") == "article:42:detail"
    assert m.cache_key("", "user", 0) == "user:0"


def test_cache_aside_roundtrip():
    store = m.MemoryStore()
    calls = {"n": 0}

    def loader():
        calls["n"] += 1
        return {"name": "华水", "n": 1}

    value, hit = m.get_or_load(store, "user:1", loader, ttl=60)
    assert (value, hit) == ({"name": "华水", "n": 1}, False)
    value2, hit2 = m.get_or_load(store, "user:1", loader, ttl=60)
    assert (value2, hit2) == ({"name": "华水", "n": 1}, True)
    assert calls["n"] == 1


def test_null_cache_blocks_penetration():
    store = m.MemoryStore()
    calls = {"n": 0}

    def missing():
        calls["n"] += 1
        return None

    assert m.get_or_load_with_null(store, "user:404", missing) == (None, False)
    assert m.get_or_load_with_null(store, "user:404", missing) == (None, True)
    assert m.get_or_load_with_null(store, "user:404", missing) == (None, True)
    assert calls["n"] == 1, "空结果也要缓存，否则就是缓存穿透"
    assert store.get("user:404") == m.NULL_SENTINEL


def test_single_flight_lets_only_one_thread_load():
    store = m.MemoryStore()
    calls = {"n": 0}
    results: list[dict] = []

    def loader():
        calls["n"] += 1
        time.sleep(0.05)
        return {"value": "expensive"}

    def worker():
        results.append(m.single_flight(store, "hot:key", loader, ttl=30, lock_ttl=5, wait=0.01))

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(results) == 8
    assert all(item == {"value": "expensive"} for item in results)
    assert calls["n"] == 1, f"热点 key 只应该有一次回源，实际 {calls['n']} 次"


def test_jittered_ttl_spreads_expiry():
    samples = [m.jittered_ttl(100, ratio=0.2) for _ in range(200)]
    assert all(80 <= value <= 120 for value in samples)
    assert len(set(samples)) > 100, "必须真的随机，不能每次都返回同一个数"
    assert abs(sum(samples) / len(samples) - 100) < 5


def test_distributed_lock_mutual_exclusion():
    clock = FakeClock()
    store = m.MemoryStore(clock=clock)
    first = m.DistributedLock(store, "lock:job", ttl=5)
    second = m.DistributedLock(store, "lock:job", ttl=5)
    assert first.acquire() is True
    assert second.acquire() is False, "锁被占用时不能重复获取"
    assert first.release() is True
    assert second.acquire() is True
    assert store.delete_if_value("lock:job", "别人的 token") is False
    assert second.release() is True

    third = m.DistributedLock(store, "lock:job", ttl=5)
    assert third.acquire() is True
    clock.advance(6)  # 锁自动过期，避免死锁
    fourth = m.DistributedLock(store, "lock:job", ttl=5)
    assert fourth.acquire() is True


def test_lock_context_manager():
    store = m.MemoryStore()
    with m.DistributedLock(store, "lock:x", ttl=5) as lock:
        assert store.exists(lock.key) is True
    assert store.exists("lock:x") is False

    with m.DistributedLock(store, "lock:y", ttl=5):
        try:
            with m.DistributedLock(store, "lock:y", ttl=5):
                raise AssertionError("不应该执行到这里")
        except RuntimeError:
            pass


def test_redis_release_lua_is_compare_and_delete():
    script = m.redis_release_lua()
    assert "KEYS[1]" in script and "ARGV[1]" in script
    assert "redis.call('get'" in script
    assert "del" in script


def test_idempotent_executes_once_until_ttl():
    clock = FakeClock()
    store = m.MemoryStore(clock=clock)
    calls = {"n": 0}

    def action():
        calls["n"] += 1
        return {"order": "paid"}

    assert m.idempotent(store, "pay:order-1", action, ttl=60) == ("executed", {"order": "paid"})
    assert m.idempotent(store, "pay:order-1", action, ttl=60) == ("replayed", {"order": "paid"})
    assert calls["n"] == 1
    clock.advance(61)
    assert m.idempotent(store, "pay:order-1", action, ttl=60)[0] == "executed"
    assert calls["n"] == 2


def test_rate_limit_fixed_window():
    clock = FakeClock()
    store = m.MemoryStore(clock=clock)
    assert m.rate_limit(store, "api:u1", limit=3, window=10) == (True, 1)
    assert m.rate_limit(store, "api:u1", limit=3, window=10) == (True, 2)
    assert m.rate_limit(store, "api:u1", limit=3, window=10) == (True, 3)
    allowed, count = m.rate_limit(store, "api:u1", limit=3, window=10)
    assert allowed is False and count == 4
    clock.advance(10.1)
    assert m.rate_limit(store, "api:u1", limit=3, window=10) == (True, 1)
