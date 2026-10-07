"""第 5 章：类型注解、Protocol 泛型、Pydantic 校验、结构化日志、文件读写

零基础先修：先完成第 1–4 章；注解语法本身零基础也能看懂，难的是背后的类型思维。

目标：写出**接口清晰、参数可控、日志可检索**的代码。这是后端工程师的日常形态。

本章的注解不是为了“好看”，而是为了三件事：

1. 让 IDE 和 mypy 提前发现错误；
2. 用 Protocol 表达“我只要你长这样”，实现松耦合（依赖注入的基础）；
3. 用 Pydantic 在系统边界（HTTP 请求、LLM 结构化输出）做一次性校验。
"""

from __future__ import annotations

import json
import logging
import os
from collections.abc import Callable, Iterator, Sequence
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Generic, Protocol, TypeVar, runtime_checkable

T = TypeVar("T")
R = TypeVar("R")

# 请求级上下文：并发处理多个请求时，每条日志都能带上自己的 request_id
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


def set_request_id(value: str) -> Token[str]:
    """设置当前上下文的 request_id 并返回 token（用于 reset）。"""
    raise NotImplementedError("TODO")


def current_request_id() -> str:
    raise NotImplementedError("TODO")


@dataclass
class Page(Generic[T]):
    """分页结果：``items`` / ``total`` / ``page`` / ``size``，并实现 ``pages`` 属性。"""

    items: list[T]
    total: int
    page: int
    size: int

    @property
    def pages(self) -> int:
        """总页数：向上取整，total=0 时为 0。"""
        raise NotImplementedError("TODO")


def paginate(items: Sequence[T], page: int, size: int) -> Page[T]:
    """1 起始的分页：

    - ``page < 1`` 或 ``size < 1`` 或 ``size > 100`` 抛 ValueError
    - 超出范围的页返回空 ``items``，但 ``total`` / ``pages`` 仍然正确
    """
    raise NotImplementedError("TODO")


def map_page(page: Page[T], func: Callable[[T], R]) -> Page[R]:
    """把 Page 里的元素映射成另一种类型，保留分页信息。"""
    raise NotImplementedError("TODO")


@runtime_checkable
class Repository(Protocol):
    """仓储协议：只要求“长这样”，不要求继承。"""

    def get(self, key: str) -> dict[str, Any] | None: ...

    def save(self, key: str, value: dict[str, Any]) -> None: ...

    def keys(self) -> list[str]: ...


class InMemoryRepo:
    """内存实现：``save`` 时存一份**拷贝**，避免外部改了字典却以为已经落库。"""

    def __init__(self) -> None:
        raise NotImplementedError("TODO")

    def get(self, key: str) -> dict[str, Any] | None:
        raise NotImplementedError("TODO")

    def save(self, key: str, value: dict[str, Any]) -> None:
        raise NotImplementedError("TODO")

    def keys(self) -> list[str]:
        raise NotImplementedError("TODO")


def sync_all(repo: Repository) -> list[str]:
    """把仓储里所有记录跑一遍“同步”，返回处理过的 key（按字典序）。

    这个函数只依赖 Protocol 定义的方法，任何满足协议的实现都能传进来。
    """
    raise NotImplementedError("TODO")


def validate_user(raw: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    """手写校验（不用 Pydantic），返回 (清洗后的数据, 错误列表)。

    规则（错误信息里必须包含字段名，顺序固定 name -> age -> email）：

    - ``name``：字符串，strip 后不能为空，否则错误 ``"name: 不能为空"``
    - ``age``：可以缺省；给了就必须是 1..150 的 int（bool 不算 int），
      否则错误 ``"age: 必须是 1-150 的整数"``
    - ``email``：必须是非空字符串且含 ``@``，否则 ``"email: 格式不正确"``

    有错误时第一部分返回 None。
    """
    raise NotImplementedError("TODO: 先收集 errors，再决定返回什么")


def write_json_atomic(path: Path, data: Any) -> None:
    """原子写 JSON：先写同目录临时文件，再 ``os.replace`` 覆盖目标。

    要求 UTF-8、``ensure_ascii=False``、缩进 2，文件名形如 ``<name>.tmp``，写完不能留下临时文件。
    """
    raise NotImplementedError("TODO")


def read_json(path: Path) -> Any:
    """读 JSON；文件不存在时抛 FileNotFoundError（不要吞掉）。"""
    raise NotImplementedError("TODO")


class JsonFormatter(logging.Formatter):
    """把日志格式化成一行 JSON。字段至少包含：

    ``ts`` / ``level`` / ``logger`` / ``message`` / ``request_id``，
    另外把 ``record.fields`` 里的键值平铺进去。
    """

    def format(self, record: logging.LogRecord) -> str:
        raise NotImplementedError("TODO")


def setup_json_logger(name: str, stream: Any, level: int = logging.INFO) -> logging.Logger:
    """创建/复用 logger：只挂一个 handler，写 JSON，且不向 root 传播（避免重复输出）。"""
    raise NotImplementedError("TODO")


def log_event(logger: logging.Logger, message: str, **fields: Any) -> None:
    """打一条带自定义字段的 INFO 日志，自动带上当前 request_id。"""
    raise NotImplementedError("TODO: logger.info(message, extra={...})")


try:  # Pydantic 是阶段一的依赖，没装也不该让整个模块 import 失败
    from pydantic import BaseModel, Field, field_validator

    _HAS_PYDANTIC = True
except ImportError:  # pragma: no cover
    _HAS_PYDANTIC = False

if _HAS_PYDANTIC:

    class UserModel(BaseModel):
        """Pydantic v2 版本的用户模型，规则与 ``validate_user`` 一致。

        - ``name``：str，去空白后不能为空
        - ``age``：int | None，范围 1..150
        - ``email``：str，必须含 "@"
        """

        name: str
        age: int | None = Field(default=None, ge=1, le=150)
        email: str

        @field_validator("name")
        @classmethod
        def _check_name(cls, value: str) -> str:
            raise NotImplementedError("TODO")

        @field_validator("email")
        @classmethod
        def _check_email(cls, value: str) -> str:
            raise NotImplementedError("TODO")
