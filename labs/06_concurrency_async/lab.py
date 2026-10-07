"""第 6 章：并发与异步（GIL、线程、进程、asyncio）

零基础先修：必须完成第 1–4 章（尤其是异常与生成器），否则异步会变成背语法。

目标：面对“慢”的时候，能判断该用多线程、多进程还是 asyncio，并写出不阻塞的异步代码。

判断口诀（先记住，第 7 章再拆原理）：

- **IO 密集**（网络、磁盘、数据库）：线程 或 asyncio
- **CPU 密集**（计算、加密、图片处理）：多进程（或 C 扩展/Cython）
- 高并发长连接服务：asyncio

手动实践：跑 ``python labs/06_concurrency_async/demo_gil.py``，亲眼看到 CPU 密集任务用线程并不会更快。
"""

from __future__ import annotations

import asyncio
import queue
import threading
import time
from collections.abc import Callable, Coroutine, Sequence
from concurrent.futures import ThreadPoolExecutor
from functools import partial, wraps
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def run_serial(delays: Sequence[float]) -> float:
    """串行 sleep 所有延迟，返回总耗时（秒）。这是“没有并发”的基线。"""
    raise NotImplementedError("TODO: 用 time.perf_counter 记时")


def run_threads(delays: Sequence[float], workers: int = 4) -> float:
    """用 ``ThreadPoolExecutor`` 并发跑，返回总耗时。IO 密集任务应该显著快于串行。"""
    raise NotImplementedError("TODO: executor.map 或 submit 都可以")


class SafeCounter:
    """线程安全计数器：``increment(amount=1)`` + ``value`` 属性。

    要求用 ``threading.Lock`` 保护 ``+=``。不做保护时，100 个线程各加 1000 次的结果通常小于期望值
    （读-改-写三步被打断），你可以自己去验证。
    """

    def __init__(self) -> None:
        raise NotImplementedError("TODO")

    def increment(self, amount: int = 1) -> None:
        raise NotImplementedError("TODO")

    @property
    def value(self) -> int:
        raise NotImplementedError("TODO")


def producer_consumer(items: Sequence[int], workers: int = 3) -> int:
    """生产者-消费者：主线程把 items 放进 ``queue.Queue``，workers 个线程取出并求和，返回总和。

    ``queue.Queue`` 本身线程安全，这也是“不要用裸 list 做任务队列”的原因。
    """
    raise NotImplementedError("TODO")


async def fake_fetch(index: int, delay: float) -> str:
    """模拟一次网络请求：等 delay 秒后返回 ``f"done-{index}"``。"""
    raise NotImplementedError("TODO: await asyncio.sleep(delay)")


async def fetch_all(delays: Sequence[float]) -> list[str]:
    """并发发起所有请求（``asyncio.gather``），**结果顺序与输入一致**。"""
    raise NotImplementedError("TODO")


async def fetch_with_limit(delays: Sequence[float], limit: int) -> tuple[list[str], int]:
    """带并发上限的批量请求，返回 (结果列表, 观察到的最大并发数)。

    要求用 ``asyncio.Semaphore(limit)`` 限流，并在任务内部统计真实并发峰值。
    """
    raise NotImplementedError("TODO")


async def get_or_timeout(delay: float, timeout: float) -> str:
    """delay 秒后返回 "done"；超过 timeout 抛 ``asyncio.TimeoutError``（用 asyncio.wait_for）。"""
    raise NotImplementedError("TODO")


async def run_blocking_in_executor(func: Callable[..., Any], *args: Any) -> Any:
    """把阻塞函数丢到线程池执行，避免卡住事件循环（``loop.run_in_executor``）。"""
    raise NotImplementedError("TODO")


def async_retry(
    times: int = 3,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
    delay: float = 0.0,
    backoff: float = 1.0,
) -> Callable[[F], F]:
    """异步版重试装饰器。语义与第 2 章的 ``retry`` 一致，但等待要用 ``await asyncio.sleep``。"""
    raise NotImplementedError("TODO")


async def gather_with_errors(delays: Sequence[float]) -> dict[str, list[Any]]:
    """并发执行，但**不要因为一个任务失败就整体失败**：

    - 负数 delay 视为失败任务（抛 ``ValueError``），其余正常返回 "done-i"
    - 返回 ``{"ok": [...成功结果...], "errors": [...异常对象...]}``（各自保持输入顺序）
    """
    raise NotImplementedError("TODO: gather(..., return_exceptions=True) 然后分类")
