"""第 3 章参考实现。"""

from __future__ import annotations

import math
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from functools import total_ordering


class Vector:
    __slots__ = ("x", "y")

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    def __add__(self, other: Vector) -> Vector:
        if not isinstance(other, Vector):
            return NotImplemented
        return Vector(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vector) -> Vector:
        if not isinstance(other, Vector):
            return NotImplemented
        return Vector(self.x - other.x, self.y - other.y)

    def __mul__(self, k: float) -> Vector:
        return Vector(self.x * k, self.y * k)

    def __rmul__(self, k: float) -> Vector:
        return self * k

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vector):
            return NotImplemented
        return (self.x, self.y) == (other.x, other.y)

    def __hash__(self) -> int:
        return hash((self.x, self.y))

    def __abs__(self) -> float:
        return math.hypot(self.x, self.y)

    def __repr__(self) -> str:
        return f"Vector({self.x:g}, {self.y:g})"


class CurrencyMismatchError(ValueError):
    pass


@total_ordering
@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str = "CNY"

    def __add__(self, other: Money) -> Money:
        if not isinstance(other, Money):
            return NotImplemented
        self._check_currency(other)
        return Money(self.amount + other.amount, self.currency)

    def __lt__(self, other: Money) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        self._check_currency(other)
        return self.amount < other.amount

    def _check_currency(self, other: Money) -> None:
        if self.currency != other.currency:
            raise CurrencyMismatchError(f"币种不一致: {self.currency} vs {other.currency}")

    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"


class TraceMixin:
    def __init__(self, *args: object, **kwargs: object) -> None:
        self.trace: list[str] = []
        self.trace.append("TraceMixin")
        super().__init__(*args, **kwargs)  # type: ignore[misc]


class CacheMixin:
    def __init__(self, *args: object, **kwargs: object) -> None:
        self.cache: dict[str, object] = {}
        self.trace.append("CacheMixin")
        super().__init__(*args, **kwargs)  # type: ignore[misc]

    def build_cache_key(self, key: str) -> str:
        return f"{self.name}:{key}"


class BaseRepo:
    def __init__(self, name: str, *args: object, **kwargs: object) -> None:
        self.name = name
        self.trace.append("BaseRepo")
        super().__init__(*args, **kwargs)


class ArticleRepo(TraceMixin, CacheMixin, BaseRepo):
    def __init__(self, name: str = "articles") -> None:
        super().__init__(name)
        self.trace.append("ArticleRepo")


class Positive:
    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name
        self.storage = f"_{name}"

    def __get__(self, instance: object, owner: type | None = None) -> object:
        if instance is None:
            return self
        return instance.__dict__[self.storage]  # type: ignore[attr-defined]

    def __set__(self, instance: object, value: object) -> None:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(f"{self.name} 必须是数字，收到 {type(value).__name__}")
        if value <= 0:
            raise ValueError(f"{self.name} 必须大于 0，收到 {value}")
        instance.__dict__[self.storage] = value  # type: ignore[attr-defined]


class Product:
    price = Positive()

    def __init__(self, name: str, price: float) -> None:
        self.name = name
        self.price = price

    def __repr__(self) -> str:
        return f"Product(name={self.name!r}, price={self.price})"


class Shape(ABC):
    @abstractmethod
    def area(self) -> float:
        ...

    def describe(self) -> str:
        return f"{type(self).__name__}(area={self.area():.2f})"


class Circle(Shape):
    def __init__(self, radius: float) -> None:
        self.radius = radius

    def area(self) -> float:
        return math.pi * self.radius**2


class Rect(Shape):
    def __init__(self, width: float, height: float) -> None:
        self.width = width
        self.height = height

    def area(self) -> float:
        return self.width * self.height


def total_area(shapes: list[Shape]) -> float:
    return sum(shape.area() for shape in shapes)


class User:
    def __init__(self, name: str, email: str) -> None:
        self.name = name
        self.email = email

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("name 不能为空")
        self._name = cleaned

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        if "@" not in value:
            raise ValueError(f"非法邮箱: {value!r}")
        self._email = value

    def __repr__(self) -> str:
        return f"User(name={self._name!r}, email={self._email!r})"


class DictPoint:
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y


class SlotsPoint:
    __slots__ = ("x", "y")

    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y


def instance_sizes() -> tuple[int, int]:
    return sys.getsizeof(DictPoint(1, 2)), sys.getsizeof(SlotsPoint(1, 2))


class Multiplier:
    def __init__(self, factor: int) -> None:
        self.factor = factor

    def __call__(self, value: int) -> int:
        return self.factor * value
