"""第 7 章：Python 原理（对象模型、内存、字节码、属性查找、拷贝）

零基础先修：本章是「解释为什么」，先把第 1–4 章的代码写熟再来，效果最好。

目标：能解释面试里那些“为什么”，并且知道它们的工程后果。

这些问题在真实开发里的价值是：

- 知道 ``is`` 和 ``==`` 的区别，才不会写出偶发 bug；
- 知道默认参数只在定义时求值一次，才不会让缓存串数据；
- 知道循环引用要靠 gc 回收，才不会在长生命周期对象里堆内存；
- 知道属性查找顺序，才能理解 ``__slots__``、描述符、ORM 的字段声明。
"""

from __future__ import annotations

import dis
import gc
import sys
import timeit
import weakref
from collections.abc import Callable
from typing import Any


def int_interning() -> tuple[bool, bool]:
    """返回 (小整数是否同一对象, 运行时构造的大整数是否同一对象)。

    提示：CPython 缓存 -5..256 的小整数；``int("1000")`` 每次都会新建对象。
    """
    raise NotImplementedError("TODO")


def string_interning() -> tuple[bool, bool]:
    """返回 (两个相同字面量是否同一对象, 运行时拼接出的字符串是否同一对象)。

    提示：``"".join(["a", "b", "c"]) is "abc"``。
    """
    raise NotImplementedError("TODO")


def refcount_grows() -> tuple[int, int]:
    """返回 (只有 1 个引用时的 getrefcount, 再多加 1 个引用后的 getrefcount)。"""
    raise NotImplementedError("TODO")


def cycle_is_collected() -> tuple[bool, bool]:
    """返回 (创建循环引用后 gc 是否回收了它们, 对象是否被 gc 跟踪)。

    要求：用 ``gc.collect()`` 的返回值判断；用 ``gc.is_tracked`` 判断跟踪状态。
    """
    raise NotImplementedError("TODO")


def mutable_default_trap() -> Callable[[str], list[str]]:
    """返回一个**故意写错**的函数：``def f(item, acc=[])`` 那种，用来复现默认参数共享问题。

    测试会连续调用两次，第二次能看到第一次的结果。
    """
    raise NotImplementedError("TODO")


def mutable_default_fixed() -> Callable[[str], list[str]]:
    """返回修好的版本：每次调用都不共享状态。"""
    raise NotImplementedError("TODO")


def bytecode_ops(func: Callable[..., Any], recursive: bool = False) -> list[str]:
    """返回函数字节码里的指令名列表（用 ``dis.get_instructions``）。

    ``recursive=True`` 时，还要把内嵌的 code object（编译期生成的子函数/推导式）里的指令也加进来。
    这能解释一个现象：Python 3.11 里列表推导式会编译成独立的 ``<listcomp>`` code object，
    而 3.12 起的内联实现（PEP 709）把 ``LIST_APPEND`` 放进了外层函数。
    """
    raise NotImplementedError("TODO: instruction.argval 是 code object 时递归进去")


class LazyConfig:
    """演示 ``__getattr__`` 与 ``__getattribute__`` 的分工：

    - 属性第一次被访问时才计算（惰性），结果写进 ``self.cache``；
    - 第二次访问应直接命中 cache 的语义；
    - 模拟昂贵加载：返回值形如 ``{"region": "cn", "<属性名>": VALUE_UPPER}``；
    - 用 ``loads`` 计数，记录真正加载了几次。
    """

    def __init__(self, source: dict[str, str]) -> None:
        raise NotImplementedError("TODO")

    def __getattr__(self, name: str) -> Any:
        raise NotImplementedError("TODO: 注意别把内部属性也拦截了，否则会无限递归")


def copy_semantics() -> tuple[list[Any], list[Any], list[Any]]:
    """返回 (浅拷贝后被改动的原对象, 浅拷贝结果, 深拷贝结果)。

    要求：

    - 原对象 ``original = [[1], 2]``
    - 浅拷贝后给内层 list 追加 9
    - 深拷贝后给内层 list 追加 8
    返回 original / shallow / deep，让测试看清哪个被“连累”了。
    """
    raise NotImplementedError("TODO")


class Big:
    """用来被弱引用缓存的对象。"""

    def __init__(self, name: str) -> None:
        self.name = name


def weak_cache_roundtrip() -> tuple[int, int]:
    """用 ``weakref.WeakValueDictionary`` 做缓存，返回 (放入后的长度, 强引用消失后的长度)。

    要求：取出外部强引用并 ``gc.collect()`` 之后，缓存长度应该回到 0（或至少小于放入时）。
    """
    raise NotImplementedError("TODO")


def benchmark(func: Callable[[], Any], number: int = 1000) -> float:
    """用 ``timeit.timeit`` 测 func 执行 number 次的总耗时。"""
    raise NotImplementedError("TODO")
