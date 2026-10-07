"""第 5 章测试：泛型分页、Protocol、校验、日志、原子写文件。"""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from learnkit import load

m = load("05_typing_log")


def test_paginate_and_pages():
    items = list(range(1, 11))
    page = m.paginate(items, page=1, size=3)
    assert page.items == [1, 2, 3]
    assert (page.total, page.pages, page.page, page.size) == (10, 4, 1, 3)
    assert m.paginate(items, page=4, size=3).items == [10]
    assert m.paginate(items, page=9, size=3).items == []
    assert m.paginate([], page=1, size=3).pages == 0
    for bad in (0, -1):
        with pytest.raises(ValueError):
            m.paginate(items, page=bad, size=3)
    for bad_size in (0, 101):
        with pytest.raises(ValueError):
            m.paginate(items, page=1, size=bad_size)


def test_map_page_keeps_pagination():
    page = m.paginate([1, 2, 3], page=2, size=2)
    mapped = m.map_page(page, lambda n: f"#{n}")
    assert mapped.items == ["#3"]
    assert (mapped.total, mapped.page, mapped.size, mapped.pages) == (3, 2, 2, 2)


def test_repository_protocol_and_isolation():
    repo = m.InMemoryRepo()
    assert isinstance(repo, m.Repository), "runtime_checkable 协议可以做结构检查"
    payload = {"name": "Ann"}
    repo.save("1", payload)
    payload["name"] = "被外部改掉了"
    assert repo.get("1") == {"name": "Ann"}, "存进去的应该是拷贝"
    got = repo.get("1")
    assert got is not None
    got["name"] = "改了返回值"
    assert repo.get("1") == {"name": "Ann"}, "取出来的也应该是拷贝"


def test_sync_all_uses_only_protocol():
    class FakeRepo:
        def __init__(self) -> None:
            self.data = {"b": {"v": 2}, "a": {"v": 1}}

        def get(self, key):
            return dict(self.data[key])

        def save(self, key, value):
            self.data[key] = value

        def keys(self):
            return list(self.data)

    fake = FakeRepo()
    assert m.sync_all(fake) == ["a", "b"]
    assert fake.data["a"]["synced"] is True


def test_validate_user_collects_all_errors_in_order():
    data, errors = m.validate_user({"name": "  Ann ", "age": 30, "email": "a@b.c"})
    assert data == {"name": "Ann", "age": 30, "email": "a@b.c"}
    assert errors == []

    data2, errors2 = m.validate_user({"name": "   ", "age": True, "email": "nope"})
    assert data2 is None
    assert errors2 == ["name: 不能为空", "age: 必须是 1-150 的整数", "email: 格式不正确"]

    data3, errors3 = m.validate_user({"name": "Ann", "email": "a@b.c"})
    assert errors3 == [] and data3 is not None and "age" not in data3


def test_pydantic_model():
    pytest.importorskip("pydantic")
    assert hasattr(m, "UserModel")
    model = m.UserModel(name=" Ann ", age=20, email="a@b.c")
    assert model.name == "Ann"
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        m.UserModel(name="  ", email="a@b.c")
    with pytest.raises(ValidationError):
        m.UserModel(name="Ann", age=999, email="a@b.c")
    with pytest.raises(ValidationError):
        m.UserModel(name="Ann", email="nope")


def test_json_logger_single_handler_and_fields():
    stream = io.StringIO()
    logger = m.setup_json_logger("learnkit.test", stream)
    logger = m.setup_json_logger("learnkit.test", stream)
    assert len(logger.handlers) == 1, "重复调用不能叠加 handler"

    m.log_event(logger, "开始处理", user_id="u1")
    payload = json.loads(stream.getvalue().strip().splitlines()[0])
    assert payload["message"] == "开始处理"
    assert payload["request_id"] == "-"
    assert payload["user_id"] == "u1"
    assert payload["level"] == "INFO"
    assert payload["logger"] == "learnkit.test"


def test_request_id_context():
    token = m.set_request_id("req-123")
    assert m.current_request_id() == "req-123"
    m.request_id_var.reset(token)
    assert m.current_request_id() == "-"


def test_atomic_json_roundtrip(tmp_path: Path):
    target = tmp_path / "data.json"
    m.write_json_atomic(target, {"名称": "华水", "n": 1})
    assert m.read_json(target) == {"名称": "华水", "n": 1}
    assert target.read_text(encoding="utf-8").startswith("{")
    leftovers = [p.name for p in tmp_path.iterdir() if p.suffix == ".tmp"]
    assert leftovers == []
    with pytest.raises(FileNotFoundError):
        m.read_json(tmp_path / "missing.json")
