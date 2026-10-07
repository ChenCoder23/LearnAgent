"""第 3 章：面向对象与魔术方法

零基础先修：至少完成 labs/00a–00c，并做掉第 1、2 章，再来碰类和继承。

目标：写出“**像内置类型一样好用**”的自定义类型，并能解释 MRO 与 ``super()`` 的协作式初始化。

本章直接对应后端开发里的实体类（Entity）、值对象（Value Object）、仓储基类（Repository）。
"""

from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from functools import total_ordering


class Vector:
    """二维向量：不可变值对象。需要实现：

    - ``__init__(self, x, y)``：保存为只读属性
    - ``__add__`` / ``__sub__``：向量加减，返回新的 Vector
    - ``__mul__(self, k)`` / ``__rmul__``：数乘，支持 ``2 * v``
    - ``__eq__``：按值比较；``__hash__``：同值同哈希（可放进 set）
    - ``__abs__``：模长 sqrt(x^2 + y^2)
    - ``__repr__``：形如 ``Vector(1, 2)``
    """

    def __init__(self, x: float, y: float) -> None:
        raise NotImplementedError("TODO")

    def __add__(self, other: Vector) -> Vector:
        raise NotImplementedError("TODO")

    def __sub__(self, other: Vector) -> Vector:
        raise NotImplementedError("TODO")

    def __mul__(self, k: float) -> Vector:
        raise NotImplementedError("TODO")

    def __rmul__(self, k: float) -> Vector:
        raise NotImplementedError("TODO")

    def __eq__(self, other: object) -> bool:
        raise NotImplementedError("TODO")

    def __hash__(self) -> int:
        raise NotImplementedError("TODO")

    def __abs__(self) -> float:
        raise NotImplementedError("TODO")

    def __repr__(self) -> str:
        raise NotImplementedError("TODO")


class CurrencyMismatchError(ValueError):
    """币种不一致时抛出。"""


@total_ordering
@dataclass(frozen=True)
class Money:
    """金额值对象：``Money(Decimal("10.00"), "CNY")``。

    - 用 ``frozen=True`` 保证不可变（哈希与比较才安全）。
    - 实现 ``__add__``：币种不同抛 ``CurrencyMismatchError``。
    - 实现 ``__lt__``；``functools.total_ordering`` 会自动补全其他比较运算。
    - 金额一律用 ``Decimal``，不要用 float。
    """

    amount: Decimal
    currency: str = "CNY"

    def __add__(self, other: Money) -> Money:
        raise NotImplementedError("TODO: 检查币种，再返回新的 Money")

    def __lt__(self, other: Money) -> bool:
        raise NotImplementedError("TODO: 币种不同怎么办？先想清楚规则，再和测试对齐")


class TraceMixin:
    """把 ``trace`` 列表接进协作式初始化链条。

    约定（很重要）：**先 append 自己的名字，再调用 ``super().__init__()``**，
    这样 trace 记录的是“进入顺序”，和 MRO 顺序一致。
    所有 ``__init__`` 都必须写成 ``def __init__(self, *args, **kwargs)`` 并把参数转发给 super，
    否则参数传不到 MRO 链条的下一环。
    """

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise NotImplementedError("TODO")


class CacheMixin:
    """给仓储加一层内存缓存：``build_cache_key(self, key) -> str``。实现 super 链。"""

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise NotImplementedError("TODO")

    def build_cache_key(self, key: str) -> str:
        raise NotImplementedError("TODO: 形如 'articles:42'")


class BaseRepo:
    """最底层：设置 ``self.name``，并把 'BaseRepo' 记进 trace。"""

    def __init__(self, name: str, *args: object, **kwargs: object) -> None:
        raise NotImplementedError("TODO")


class ArticleRepo(TraceMixin, CacheMixin, BaseRepo):
    """最终类：``ArticleRepo("articles")`` 必须让 trace 等于
    ``["TraceMixin", "CacheMixin", "BaseRepo", "ArticleRepo"]``。

    提示：每个 ``__init__`` 都要调用 ``super().__init__()``，且参数要能沿着 MRO 传下去。
    """

    def __init__(self, name: str = "articles") -> None:
        raise NotImplementedError("TODO")


class Positive:
    """属性描述符：只允许正数。

    要求：

    - ``__set_name__`` 已经帮你写好（它把属性名记下来，因为描述符**无法从 self 知道**自己被赋给了哪个名字）；
    - 你要实现 ``__get__`` / ``__set__``：读写在实例 ``__dict__``，非数字或 <= 0 抛 ``ValueError``。
    """

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name
        self.storage = f"_{name}"  # 存进实例字典时换个键名，避免与类属性同名递归

    def __get__(self, instance: object, owner: type | None = None) -> object:
        raise NotImplementedError("TODO")

    def __set__(self, instance: object, value: object) -> None:
        raise NotImplementedError("TODO")


class Product:
    """用法：``Product("键盘", 199)``；``product.price = -1`` 必须抛 ValueError。"""

    price = Positive()

    def __init__(self, name: str, price: float) -> None:
        raise NotImplementedError("TODO")


class Shape(ABC):
    """抽象基类：``Shape()`` 直接实例化必须抛 TypeError。"""

    @abstractmethod
    def area(self) -> float:
        ...

    def describe(self) -> str:
        return f"{type(self).__name__}(area={self.area():.2f})"


class Circle(Shape):
    def __init__(self, radius: float) -> None:
        raise NotImplementedError("TODO")

    def area(self) -> float:
        raise NotImplementedError("TODO")


class Rect(Shape):
    def __init__(self, width: float, height: float) -> None:
        raise NotImplementedError("TODO")

    def area(self) -> float:
        raise NotImplementedError("TODO")


def total_area(shapes: list[Shape]) -> float:
    """多态求和：传进来的是 Circle 还是 Rect 都不用判断类型。"""
    raise NotImplementedError("TODO")


class User:
    """带校验的实体类：

    - ``name``：去首尾空白，空字符串抛 ValueError，通过 property + setter 校验
    - ``email``：必须含 "@"，否则抛 ValueError
    - ``__repr__`` 形如 ``User(name='Ann', email='a@b.c')``
    """

    def __init__(self, name: str, email: str) -> None:
        raise NotImplementedError("TODO")

    @property
    def name(self) -> str:
        raise NotImplementedError("TODO")

    @name.setter
    def name(self, value: str) -> None:
        raise NotImplementedError("TODO")

    @property
    def email(self) -> str:
        raise NotImplementedError("TODO")

    @email.setter
    def email(self, value: str) -> None:
        raise NotImplementedError("TODO")

    def __repr__(self) -> str:
        raise NotImplementedError("TODO")


class DictPoint:
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y


class SlotsPoint:
    """用 ``__slots__`` 去掉实例字典，省内存。"""

    __slots__ = ("x", "y")

    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y


def instance_sizes() -> tuple[int, int]:
    """返回 (普通实例字节数, __slots__ 实例字节数)，用 ``sys.getsizeof`` 取。"""
    raise NotImplementedError("TODO")


class Multiplier:
    """可调用对象：``Multiplier(3)(4) == 12``。实现 ``__call__``。"""

    def __init__(self, factor: int) -> None:
        raise NotImplementedError("TODO")

    def __call__(self, value: int) -> int:
        raise NotImplementedError("TODO")
