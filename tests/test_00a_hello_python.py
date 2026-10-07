"""阶段零 · 第 A 章测试：变量、类型、运算、字符串。

跑法：uv run pytest tests/test_00a_hello_python.py -v
"""

from __future__ import annotations

import math

import pytest

from learnkit import load

m = load("00a_hello_python")


def test_greet_returns_greeting():
    assert m.greet("小明") == "你好，小明！"
    assert m.greet("Ann") == "你好，Ann！"


def test_add_works_for_int_and_float():
    assert m.add(1, 2) == 3
    assert m.add(1.5, 2.5) == 4.0


def test_circle_area_uses_pi():
    assert m.circle_area(1) == pytest.approx(math.pi)
    assert m.circle_area(2) == pytest.approx(math.pi * 4)


def test_celsius_to_fahrenheit():
    assert m.celsius_to_fahrenheit(0) == 32
    assert m.celsius_to_fahrenheit(100) == 212
    assert m.celsius_to_fahrenheit(37) == pytest.approx(98.6)


def test_describe_returns_type_name():
    assert m.describe(1) == "int"
    assert m.describe(1.5) == "float"
    assert m.describe("a") == "str"
    assert m.describe(True) == "bool"
    assert m.describe(None) == "NoneType"
    assert m.describe([1, 2]) == "list"
    assert m.describe({"a": 1}) == "dict"


def test_total_price_with_and_without_discount():
    assert m.total_price(10, 3) == 30
    assert m.total_price(10, 3, 0.1) == pytest.approx(27)
    assert m.total_price(3.5, 2) == pytest.approx(7.0)


def test_format_receipt_keeps_two_decimals():
    assert m.format_receipt("苹果", 3.5, 2) == "苹果 x2 = 7.00 元"
    assert m.format_receipt("牛奶", 12.345, 1) == "牛奶 x1 = 12.35 元"


def test_to_int_converts_or_raises():
    assert m.to_int("12") == 12
    with pytest.raises(ValueError):
        m.to_int("abc")


def test_is_adult_boundary():
    assert m.is_adult(18) is True
    assert m.is_adult(17) is False


def test_swap_returns_swapped_tuple():
    assert m.swap(1, 2) == (2, 1)
    assert m.swap("a", "b") == ("b", "a")


def test_average_and_empty_error():
    assert m.average([1, 2, 3]) == 2
    assert m.average([1.5, 2.5]) == 2.0
    with pytest.raises(ValueError):
        m.average([])
