"""阶段零 · 第 A 章参考实现。"""

from __future__ import annotations

import math


def greet(name: str) -> str:
    return f"你好，{name}！"


def add(a: float, b: float) -> float:
    return a + b


def circle_area(radius: float) -> float:
    return math.pi * radius**2


def celsius_to_fahrenheit(celsius: float) -> float:
    return celsius * 9 / 5 + 32


def describe(value: object) -> str:
    return type(value).__name__


def total_price(price: float, count: int, discount: float = 0.0) -> float:
    return price * count * (1 - discount)


def format_receipt(name: str, price: float, count: int) -> str:
    return f"{name} x{count} = {price * count:.2f} 元"


def to_int(text: str) -> int:
    return int(text)


def is_adult(age: int) -> bool:
    return age >= 18


def swap(a: object, b: object) -> tuple[object, object]:
    return b, a


def average(numbers: list[float]) -> float:
    if not numbers:
        raise ValueError("列表不能为空")
    return sum(numbers) / len(numbers)
