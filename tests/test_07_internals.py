"""第 7 章测试：对象模型、内存、字节码、属性查找、拷贝。"""

from __future__ import annotations

import pytest

from learnkit import load

m = load("07_internals")


def test_int_and_str_interning():
    small_same, big_same = m.int_interning()
    assert small_same is True, "小整数被 CPython 缓存"
    assert big_same is False, "运行时构造的大整数是两个对象"
    literal_same, built_same = m.string_interning()
    assert literal_same is True
    assert built_same is False


def test_refcount_increases_with_new_reference():
    base, extra = m.refcount_grows()
    assert extra == base + 1
    assert base >= 2


def test_cycle_is_collected_and_tracked():
    collected, tracked = m.cycle_is_collected()
    assert tracked is True
    assert collected is True, "循环引用靠 gc 分代回收，引用计数处理不了"


def test_mutable_default_trap_vs_fixed():
    trap = m.mutable_default_trap()
    assert trap("a") == ["a"]
    assert trap("b") == ["a", "b"], "默认参数只在函数定义时创建一次"
    fixed = m.mutable_default_fixed()
    assert fixed("a") == ["a"]
    assert fixed("b") == ["b"]


def test_bytecode_shows_loop_and_comprehension():
    def sum_loop(numbers: list[int]) -> int:
        total = 0
        for number in numbers:
            total += number
        return total

    def double_list(numbers: list[int]) -> list[int]:
        return [n * 2 for n in numbers]

    loop_ops = m.bytecode_ops(sum_loop)
    assert "FOR_ITER" in loop_ops
    comp_ops = m.bytecode_ops(double_list, recursive=True)
    assert "LIST_APPEND" in comp_ops
    assert "FOR_ITER" in comp_ops, "推导式内部的循环在子 code object 里"


def test_lazy_config_loads_once():
    config = m.LazyConfig({"name": "huashui"})
    assert config.cache == {}
    first = config.name
    assert first == {"region": "cn", "name": "HUASHUI"}
    second = config.name
    assert second == first
    assert config.loads == 1, "第二次访问不应该再加载"
    with pytest.raises(AttributeError):
        _ = config.missing


def test_copy_semantics():
    original, shallow, deep = m.copy_semantics()
    assert original[0] == [1, 9], "浅拷贝共享内层对象"
    assert shallow[0] == [1, 9]
    assert deep[0] == [1, 8], "深拷贝完全独立"
    assert original[0] is shallow[0]
    assert original[0] is not deep[0]


def test_weak_cache_releases_object():
    with_strong, after_gc = m.weak_cache_roundtrip()
    assert with_strong == 1
    assert after_gc == 0, "强引用消失后弱引用缓存自动清理"


def test_benchmark_returns_positive_time():
    elapsed = m.benchmark(lambda: sum(range(100)), number=10)
    assert elapsed > 0
