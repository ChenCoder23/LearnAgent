"""第 4 章：迭代器、生成器、上下文管理器、异常

零基础先修：先熟练 for 循环与列表（labs/00b、00c），否则生成器会很抽象。

目标：能写出**惰性、可组合、资源安全**的数据处理管线，并建立自己的异常体系。

这三件事在后端里天天出现：流式读取大文件、分批处理数据、保证事务/连接一定被释放。
"""

from __future__ import annotations

import itertools
from collections.abc import Generator, Iterable, Iterator, Sequence
from contextlib import contextmanager
from typing import Any


class Countdown:
    """倒计时迭代器：``list(Countdown(3)) == [3, 2, 1]``。

    要实现 ``__iter__`` 与 ``__next__``，耗尽后抛 ``StopIteration``。
    特别注意：迭代器是**一次性**的，第二次遍历会立刻结束——这正是它和 list 的区别。
    """

    def __init__(self, start: int) -> None:
        raise NotImplementedError("TODO")

    def __iter__(self) -> Iterator[int]:
        raise NotImplementedError("TODO")

    def __next__(self) -> int:
        raise NotImplementedError("TODO")


def take(n: int, iterable: Iterable[Any]) -> list[Any]:
    """取前 n 个元素。要能处理**无限序列**（如 ``itertools.count()``），所以不能先转 list。"""
    raise NotImplementedError("TODO: 用 for + break，或者生成器 + islice")


def sliding_window(iterable: Iterable[Any], k: int) -> Iterator[tuple[Any, ...]]:
    """滑动窗口：``list(sliding_window([1,2,3,4], 2)) == [(1,2),(2,3),(3,4)]``。

    ``k <= 0`` 抛 ValueError；``k`` 大于总长度时产出为空。
    """
    raise NotImplementedError("TODO: collections.deque(maxlen=k) 是最优雅的写法")


def read_in_batches(lines: Iterable[str], size: int) -> Iterator[list[str]]:
    """把任意可迭代的字符串按 size 分批产出，最后一批可以更短。"""
    raise NotImplementedError("TODO: 攒够 size 就 yield，循环结束后别忘了收尾")


def pipe(data: Iterable[Any], *stages: Any) -> Iterator[Any]:
    """把多个“生成器函数”串成一条惰性流水线。

    每个 stage 是形如 ``lambda src: (x * 2 for x in src)`` 的函数，
    接收一个可迭代对象，返回一个新的可迭代对象。

        >>> list(pipe([1, 2, 3], lambda src: (x + 1 for x in src)))
        [2, 3, 4]
    """
    raise NotImplementedError("TODO: current = iter(data)，再依次套上每个 stage，最后 yield from")


class Timer:
    """上下文管理器：``with Timer() as t: ...`` 之后 ``t.elapsed`` 是秒数。

    要求：即使 with 内部抛异常，也要记录耗时并把异常继续抛出去（``__exit__`` 返回 False/None）。
    """

    def __enter__(self) -> Timer:
        raise NotImplementedError("TODO")

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        raise NotImplementedError("TODO")


@contextmanager
def transaction(store: dict[str, Any]) -> Generator[dict[str, Any], None, None]:
    """最简事务：进入时快照，正常退出提交，抛异常则回滚后把异常继续抛出。

    这是 LangGraph 的 checkpointer、SQLAlchemy 的 session 都在用的模式。
    """
    raise NotImplementedError("TODO: 用 yield 把 store 交出去，except 里恢复快照再 raise")


class AppError(Exception):
    """业务异常基类。"""


class NotFoundError(AppError):
    """资源不存在。"""


class ValidationError(AppError):
    """参数校验失败。"""


def load_user(store: dict[str, dict[str, Any]], user_id: str) -> dict[str, Any]:
    """按 id 取用户：

    - 取不到 -> 抛 ``NotFoundError``，并且要用 ``raise ... from``
      把底层 ``KeyError`` 挂到 ``__cause__`` 上（方便排查根因）。
    - 取到的数据缺 ``name`` 字段 -> 抛 ``ValidationError``。
    """
    raise NotImplementedError("TODO: try/except KeyError -> raise NotFoundError(...) from error")


def parse_int(text: str, default: int = 0) -> int:
    """用 ``contextlib.suppress``（不要写 try/except 大块）把非法输入转成 default。"""
    raise NotImplementedError("TODO")


def trace_order(fail: bool) -> list[str]:
    """演示 try/except/else/finally 的执行顺序，返回被执行的语句标记。

    - 成功：``["try", "else", "finally"]``
    - 失败（fail=True 时在 try 里 raise ValueError）：``["try", "except", "finally"]``
    """
    raise NotImplementedError("TODO")


def safe_divide(a: float, b: float) -> float:
    """b 为 0 时抛 ``ValidationError("除数不能为 0")``（不要漏出原生 ZeroDivisionError）。"""
    raise NotImplementedError("TODO")


def running_average() -> Generator[float | None, float, None]:
    """支持 ``send()`` 的生成器：喂入数字，返回当前平均值。

        >>> gen = running_average()
        >>> next(gen)          # 预热，返回 None
        >>> gen.send(10)       # 10.0
        >>> gen.send(20)       # 15.0
    """
    raise NotImplementedError("TODO: value = yield 当前平均值 的形式")
