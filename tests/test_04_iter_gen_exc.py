"""第 4 章测试：迭代器、生成器、上下文管理器、异常链。"""

from __future__ import annotations

import itertools
import time

import pytest

from learnkit import load

m = load("04_iter_gen_exc")


def test_countdown_is_one_shot_iterator():
    counter = m.Countdown(3)
    assert list(counter) == [3, 2, 1]
    assert list(counter) == [], "迭代器是一次性的"
    assert list(m.Countdown(0)) == []
    assert iter(m.Countdown(2)) is not None


def test_take_handles_infinite_sequences():
    assert m.take(3, itertools.count(start=5)) == [5, 6, 7]
    assert m.take(0, [1, 2]) == []
    assert m.take(5, [1]) == [1]


def test_sliding_window():
    assert list(m.sliding_window([1, 2, 3, 4], 2)) == [(1, 2), (2, 3), (3, 4)]
    assert list(m.sliding_window([1, 2, 3], 3)) == [(1, 2, 3)]
    assert list(m.sliding_window([1, 2], 5)) == []
    with pytest.raises(ValueError):
        list(m.sliding_window([1], 0))


def test_read_in_batches():
    lines = ["a", "b", "c", "d", "e"]
    assert list(m.read_in_batches(lines, 2)) == [["a", "b"], ["c", "d"], ["e"]]
    assert list(m.read_in_batches([], 3)) == []
    with pytest.raises(ValueError):
        list(m.read_in_batches(["a"], -1))


def test_pipe_is_lazy_and_composable():
    doubled = lambda src: (x * 2 for x in src)
    plus_one = lambda src: (x + 1 for x in src)
    assert list(m.pipe([1, 2, 3], doubled, plus_one)) == [3, 5, 7]
    assert list(m.pipe([1, 2])) == [1, 2]
    assert m.take(3, m.pipe(itertools.count(), doubled)) == [0, 2, 4]

    consumed: list[int] = []

    def spy(src):
        for item in src:
            consumed.append(item)
            yield item

    lazy = m.pipe([1, 2, 3], spy, doubled)
    next(iter(lazy))
    assert consumed == [1], "流水线必须是惰性的，只取一个元素就不该消费更多"


def test_timer_context_manager():
    with m.Timer() as timer:
        time.sleep(0.02)
    assert timer.elapsed >= 0.015

    with pytest.raises(RuntimeError), m.Timer() as timer2:
        raise RuntimeError("内部异常要照常抛出")
    assert timer2.elapsed >= 0


def test_transaction_commits_and_rolls_back():
    store = {"a": 1}
    with m.transaction(store) as tx:
        tx["b"] = 2
    assert store == {"a": 1, "b": 2}

    with pytest.raises(ValueError), m.transaction(store) as tx:
        tx["c"] = 3
        raise ValueError("写入失败")
    assert store == {"a": 1, "b": 2}, "异常必须回滚"


def test_exception_hierarchy_and_cause():
    assert issubclass(m.NotFoundError, m.AppError)
    assert issubclass(m.ValidationError, m.AppError)

    store = {"1": {"name": "Ann"}}
    assert m.load_user(store, "1")["name"] == "Ann"

    with pytest.raises(m.NotFoundError) as excinfo:
        m.load_user(store, "999")
    assert isinstance(excinfo.value.__cause__, KeyError)

    with pytest.raises(m.ValidationError):
        m.load_user({"2": {"email": "x"}}, "2")


def test_parse_int_and_trace_order():
    assert m.parse_int("42") == 42
    assert m.parse_int("abc", default=-1) == -1
    assert m.trace_order(fail=False) == ["try", "else", "finally"]
    assert m.trace_order(fail=True) == ["try", "except", "finally"]


def test_safe_divide_converts_exception():
    assert m.safe_divide(6, 3) == 2
    with pytest.raises(m.ValidationError):
        m.safe_divide(1, 0)


def test_running_average_with_send():
    gen = m.running_average()
    assert next(gen) is None
    assert gen.send(10) == 10.0
    assert gen.send(20) == 15.0
    assert gen.send(30) == 20.0
