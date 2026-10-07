"""第 2 章测试：闭包、装饰器、单分派、签名检查。"""

from __future__ import annotations

import time

import pytest

from learnkit import load

m = load("02_functions")


def test_counter_uses_closure_state():
    counter = m.make_counter()
    assert (counter(), counter(), counter()) == (1, 2, 3)
    other = m.make_counter(start=10, step=-2)
    assert other() == 8
    assert counter() == 4, "两个闭包必须互不影响"


def test_make_functions_avoids_late_binding():
    funcs = m.make_functions(3)
    assert [f() for f in funcs] == [0, 1, 2]


def test_compose_order_and_identity():
    double = lambda x: x * 2
    plus3 = lambda x: x + 3
    assert m.compose(double, plus3)(5) == 16
    assert m.compose()(7) == 7
    assert m.compose(double)(4) == 8


def test_retry_bare_and_parametrized():
    state = {"calls": 0}

    @m.retry
    def flaky() -> str:
        state["calls"] += 1
        if state["calls"] < 3:
            raise ValueError("boom")
        return "ok"

    assert flaky() == "ok"
    assert state["calls"] == 3
    assert flaky.__name__ == "flaky"

    state2 = {"calls": 0}

    @m.retry(times=2, exceptions=(KeyError,), delay=0)
    def never() -> None:
        state2["calls"] += 1
        raise KeyError("nope")

    with pytest.raises(KeyError):
        never()
    assert state2["calls"] == 2


def test_retry_ignores_other_exceptions_and_keeps_cause():
    @m.retry(times=5, exceptions=(ValueError,), delay=0)
    def wrong_type() -> None:
        raise TypeError("不该被重试")

    with pytest.raises(TypeError):
        wrong_type()

    @m.retry(times=2, delay=0)
    def always_fail() -> None:
        raise ValueError("最后一次")

    with pytest.raises(ValueError) as excinfo:
        always_fail()
    assert "最后一次" in str(excinfo.value)
    assert excinfo.value.__traceback__ is not None


def test_memoize_counts_and_handles_unhashable():
    calls = {"n": 0}

    @m.memoize
    def slow(n: int) -> int:
        calls["n"] += 1
        return n * n

    assert slow(4) == 16
    assert slow(4) == 16
    assert calls["n"] == 1
    assert slow.cache_info() == {"hits": 1, "misses": 1}
    assert slow.__name__ == "slow"

    @m.memoize
    def takes_list(items: list[int]) -> int:
        return sum(items)

    assert takes_list([1, 2]) == 3
    assert takes_list([1, 2]) == 3, "不可哈希参数要退化成直接执行，而不是抛异常"


def test_memoize_caches_none():
    @m.memoize
    def returns_none() -> None:
        return None

    assert returns_none() is None
    assert returns_none() is None
    assert returns_none.cache_info()["hits"] == 1


def test_once_uses_sentinel_not_truthiness():
    calls = {"n": 0}

    @m.once
    def only_none() -> None:
        calls["n"] += 1
        return None

    only_none()
    only_none()
    assert calls["n"] == 1, "返回值是 None 时也必须只执行一次"

    @m.once
    def first_wins(x: int) -> int:
        return x * 10

    assert first_wins(1) == 10
    assert first_wins(2) == 10


def test_timed_records_elapsed():
    @m.timed
    def sleepy() -> str:
        time.sleep(0.02)
        return "done"

    assert sleepy() == "done"
    assert sleepy.last_elapsed >= 0.015
    assert sleepy.__name__ == "sleepy"


def test_to_json_like_dispatch():
    assert m.to_json_like(3) == "number:3"
    assert m.to_json_like("a") == "string:a"
    assert m.to_json_like([1, "a"]) == "array:[number:1,string:a]"
    # bool 是 int 的子类，singledispatch 会命中 int 分支
    assert m.to_json_like({"b": 2, "a": [True]}) == "object:a=array:[number:True];b=number:2"
    assert m.to_json_like(None) == "unknown:NoneType"


def test_call_with_kwargs_only_filters():
    assert m.call_with_kwargs_only(lambda a, b=1: a + b, a=1, z=9) == 2
    assert m.call_with_kwargs_only(lambda a, b=1: a + b, a=1, b=5, z=9) == 6

    def accepts_extra(a: int, **rest: object) -> int:
        return a + len(rest)

    assert m.call_with_kwargs_only(accepts_extra, a=1, z=9) == 2


def test_pipeline_timer_runs_in_order():
    stages = [lambda s: s + "b", lambda s: s + "c"]
    result, elapsed = m.pipeline_timer(stages, "a")
    assert result == "abc"
    assert elapsed >= 0
