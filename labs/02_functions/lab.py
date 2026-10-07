"""第 2 章：函数、作用域、闭包、装饰器

零基础先修：如果还不清楚怎么定义函数、参数怎么传，先做 labs/00a（讲义 docs/00a-零基础起步.md）。

目标：能熟练写出**带参数、保留元信息、可叠加**的装饰器，并说清 LEGB 与闭包变量绑定。

本章是 Python 面试的高频区，也是读框架源码的入场券。LangChain 的 ``@tool``、
FastAPI 的 ``@app.get``、pytest 的 ``@pytest.fixture`` 全是同一套机制。
"""

from __future__ import annotations

import time
from collections.abc import Callable, Iterable, Sequence
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def make_counter(start: int = 0, step: int = 1) -> Callable[[], int]:
    """返回一个闭包：每次调用返回值递增 step。第一次调用返回 ``start + step``。

    >>> c = make_counter(); c(), c(), c()
    (1, 2, 3)
    """
    raise NotImplementedError("TODO: 用 nonlocal 维护状态，不要用全局变量")


def make_functions(n: int) -> list[Callable[[], int]]:
    """返回 n 个无参函数，第 i 个函数返回 i（i 从 0 开始）。

    这是**闭包延迟绑定（late binding）**的经典坑：

        >>> funcs = [lambda: i for i in range(3)]
        >>> [f() for f in funcs]
        [2, 2, 2]

    你要写出返回 ``[0, 1, 2]`` 的版本，并想清楚为什么需要默认参数或工厂函数。
    """
    raise NotImplementedError("TODO: 用默认参数捕获当前值，或者用工厂函数产生作用域")


def compose(*funcs: Callable[[Any], Any]) -> Callable[[Any], Any]:
    """把函数组合成 ``compose(f, g)(x) == f(g(x))``，从右往左执行。

    即 ``compose()` 返回恒等函数；``compose(f)`` 返回 f 本身的行为。
    """
    raise NotImplementedError("TODO: 用 functools.reduce 和 lambda 表达")


def retry(
    func: F | None = None,
    *,
    times: int = 3,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
    delay: float = 0.0,
    backoff: float = 1.0,
) -> Callable[..., Any]:
    """可参数化、也可裸用的重试装饰器：``@retry`` 与 ``@retry(times=5)`` 都要能用。

    要求：

    - 最多执行 ``times`` 次（times=1 表示不重试）。
    - 只对 ``exceptions`` 里的异常重试，其他异常原样抛出。
    - 每次失败后 sleep ``delay``，下一次 sleep 时间乘以 ``backoff``。
    - 全部失败时把最后一次异常抛出去，保留原始 traceback（在 except 里直接 ``raise`` 即可）。
    - 用 ``functools.wraps`` 保留原函数的名字与文档。
    """
    raise NotImplementedError("TODO: 想清楚 func 为 None（带括号写法）时该返回什么")


def memoize(func: F) -> F:
    """手写缓存装饰器（不许用 functools.lru_cache）。

    - 命中缓存直接返回，不重复计算；要能缓存 ``None`` 这类返回值。
    - 参数不可哈希（如 list）时不要崩，退化成直接执行。
    - 在包装函数上暴露 ``cache_info() -> {"hits": int, "misses": int}``。
    - 保留原函数的 ``__name__``。
    """
    raise NotImplementedError("TODO: 缓存 key 用 *args, **kwargs；dict.__getitem__ 前先判断是否存在")


def once(func: F) -> F:
    """只真正执行一次，之后永远返回第一次的结果（包括结果是 None 的情况）。"""
    raise NotImplementedError("TODO: 不能用 `if result:` 判断，用哨兵对象")


def timed(func: F) -> F:
    """计时装饰器：执行原函数，并把最后一次耗时写到包装函数的 ``last_elapsed`` 属性上。

    返回原函数的结果，不改变签名行为。
    """
    raise NotImplementedError("TODO: time.perf_counter 差值；属性挂在 wrapper 上")


def to_json_like(value: Any) -> str:
    """用 ``functools.singledispatch`` 做单分派：

    - int/float -> ``"number:<值>"``
    - str -> ``"string:<值>"``
    - list/tuple -> ``"array:[<每个元素递归后的结果用 , 连接>]"``
    - dict -> ``"object:<键排序后逐个递归>``，格式 ``key=value;key=value``
    - 其他 -> ``"unknown:<类型名>"``

    想清楚 bool 该走哪个分支：``bool`` 是 ``int`` 的子类，singledispatch 按 MRO 查找，
    所以 True 会命中最接近的已注册基类。
    """
    raise NotImplementedError("TODO: 用 @singledispatch 注册各类型分支")


def call_with_kwargs_only(func: Callable[..., Any], **kwargs: Any) -> Any:
    """只把 func 签名里存在的关键字参数传进去，多余的丢掉。

    这是写插件系统 / 依赖注入时的常用技巧（FastAPI 就是这么注入依赖的）。

    >>> call_with_kwargs_only(lambda a, b=1: a + b, a=1, z=9)
    2
    """
    raise NotImplementedError("TODO: inspect.signature 拿参数名，注意 **kwargs 参数要全收")


def pipeline_timer(stages: Sequence[Callable[[Any], Any]], value: Any) -> tuple[Any, float]:
    """把 value 依次喂给 stages，返回 (结果, 总耗时秒数)。至少 3 个阶段时最能体现价值。"""
    raise NotImplementedError("TODO: 用 for 循环 + time.perf_counter，别写递归")
