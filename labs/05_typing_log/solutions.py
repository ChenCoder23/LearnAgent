"""第 5 章参考实现。"""

from __future__ import annotations

import copy
import json
import logging
import math
import os
from collections.abc import Callable, Sequence
from contextvars import ContextVar, Token
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generic, Protocol, TypeVar, runtime_checkable

T = TypeVar("T")
R = TypeVar("R")

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


def set_request_id(value: str) -> Token[str]:
    return request_id_var.set(value)


def current_request_id() -> str:
    return request_id_var.get()


@dataclass
class Page(Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int

    @property
    def pages(self) -> int:
        if self.size <= 0 or self.total <= 0:
            return 0
        return math.ceil(self.total / self.size)


def paginate(items: Sequence[T], page: int, size: int) -> Page[T]:
    if page < 1:
        raise ValueError("page 必须 >= 1")
    if size < 1 or size > 100:
        raise ValueError("size 必须在 1..100 之间")
    total = len(items)
    start = (page - 1) * size
    return Page(items=list(items[start : start + size]), total=total, page=page, size=size)


def map_page(page: Page[T], func: Callable[[T], R]) -> Page[R]:
    return Page(
        items=[func(item) for item in page.items],
        total=page.total,
        page=page.page,
        size=page.size,
    )


@runtime_checkable
class Repository(Protocol):
    def get(self, key: str) -> dict[str, Any] | None: ...

    def save(self, key: str, value: dict[str, Any]) -> None: ...

    def keys(self) -> list[str]: ...


class InMemoryRepo:
    def __init__(self) -> None:
        self._data: dict[str, dict[str, Any]] = {}

    def get(self, key: str) -> dict[str, Any] | None:
        stored = self._data.get(key)
        return copy.deepcopy(stored) if stored is not None else None

    def save(self, key: str, value: dict[str, Any]) -> None:
        self._data[key] = copy.deepcopy(value)

    def keys(self) -> list[str]:
        return list(self._data)


def sync_all(repo: Repository) -> list[str]:
    processed: list[str] = []
    for key in sorted(repo.keys()):
        record = repo.get(key)
        if record is None:
            continue
        record["synced"] = True
        repo.save(key, record)
        processed.append(key)
    return processed


def validate_user(raw: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    cleaned: dict[str, Any] = {}

    name = raw.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append("name: 不能为空")
    else:
        cleaned["name"] = name.strip()

    age = raw.get("age")
    if age is not None:
        if isinstance(age, bool) or not isinstance(age, int) or not 1 <= age <= 150:
            errors.append("age: 必须是 1-150 的整数")
        else:
            cleaned["age"] = age

    email = raw.get("email")
    if not isinstance(email, str) or "@" not in email:
        errors.append("email: 格式不正确")
    else:
        cleaned["email"] = email.strip()

    return (None, errors) if errors else (cleaned, [])


def write_json_atomic(path: Path, data: Any) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", request_id_var.get()),
        }
        payload.update(getattr(record, "fields", {}))
        return json.dumps(payload, ensure_ascii=False)


def setup_json_logger(name: str, stream: Any, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False
    for handler in list(logger.handlers):
        if getattr(handler, "_learnkit_json", False):
            logger.removeHandler(handler)
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    handler._learnkit_json = True  # type: ignore[attr-defined]
    logger.addHandler(handler)
    return logger


def log_event(logger: logging.Logger, message: str, **fields: Any) -> None:
    logger.info(message, extra={"fields": fields, "request_id": current_request_id()})


try:
    from pydantic import BaseModel, Field, field_validator

    _HAS_PYDANTIC = True
except ImportError:  # pragma: no cover
    _HAS_PYDANTIC = False

if _HAS_PYDANTIC:

    class UserModel(BaseModel):
        name: str
        age: int | None = Field(default=None, ge=1, le=150)
        email: str

        @field_validator("name")
        @classmethod
        def _check_name(cls, value: str) -> str:
            cleaned = value.strip()
            if not cleaned:
                raise ValueError("name 不能为空")
            return cleaned

        @field_validator("email")
        @classmethod
        def _check_email(cls, value: str) -> str:
            if "@" not in value:
                raise ValueError("email 格式不正确")
            return value
