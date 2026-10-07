"""第 8 章测试：服务层规则 + HTTP 接口。"""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("sqlalchemy")

from sqlalchemy.orm import sessionmaker  # noqa: E402

from learnkit import load  # noqa: E402

m = load("08_fastapi_sql")


@pytest.fixture()
def engine(tmp_path: Path):
    url = f"sqlite+pysqlite:///{(tmp_path / 'test.db').as_posix()}"
    engine = m.make_engine(url)
    m.init_db(engine)
    yield engine
    engine.dispose()


@pytest.fixture()
def service(engine):
    return m.ArticleService(sessionmaker(bind=engine, expire_on_commit=False), m.SimpleCache())


@pytest.fixture()
def client(engine):
    from fastapi.testclient import TestClient

    return TestClient(m.create_app(engine, m.SimpleCache()))


def test_tag_helpers_normalize():
    assert m.split_tags("python, fastapi ,backend,python") == ["python", "fastapi", "backend"]
    assert m.split_tags("") == []
    assert m.join_tags([" a ", "a", "b"]) == "a,b"


def test_service_create_get_and_conflict(service):
    created = service.create(m.ArticleCreate(title="第一篇", content="hello", tags=["py", "py", "db"]))
    assert created.id == 1
    assert created.tags == ["py", "db"]
    assert created.author == "anonymous"
    assert created.created_at.tzinfo is not None or created.created_at is not None

    fetched = service.get(created.id)
    assert fetched.title == "第一篇"

    with pytest.raises(m.ConflictError):
        service.create(m.ArticleCreate(title="第一篇"))


def test_service_cache_aside_and_invalidation(service):
    created = service.create(m.ArticleCreate(title="缓存", content="v1"))
    cache = service.cache
    service.get(created.id)
    service.get(created.id)
    assert cache.hits == 1 and cache.misses == 1, "第二次读应该命中缓存"

    service.update(created.id, m.ArticleUpdate(content="v2"))
    assert cache.get(m.article_cache_key(created.id)) is None, "写操作必须删缓存"
    assert service.get(created.id).content == "v2"

    service.delete(created.id)
    with pytest.raises(m.NotFoundError):
        service.get(created.id)


def test_service_pagination_and_keyword(service):
    for i in range(1, 6):
        service.create(m.ArticleCreate(title=f"文章{i}", tags=["t"]))
    page = service.list(page=2, size=2)
    assert [item.title for item in page.items] == ["文章3", "文章4"]
    assert (page.total, page.page, page.size) == (5, 2, 2)
    filtered = service.list(keyword="文章1")
    assert [item.title for item in filtered.items] == ["文章1"]
    with pytest.raises(ValueError):
        service.list(page=0)
    with pytest.raises(ValueError):
        service.list(size=1000)


def test_service_update_missing_and_conflict(service):
    first = service.create(m.ArticleCreate(title="A"))
    service.create(m.ArticleCreate(title="B"))
    with pytest.raises(m.ConflictError):
        service.update(first.id, m.ArticleUpdate(title="B"))
    with pytest.raises(m.NotFoundError):
        service.update(999, m.ArticleUpdate(title="C"))


def test_http_crud_flow(client):
    created = client.post("/articles", json={"title": "接口", "tags": ["api"]})
    assert created.status_code == 201
    article_id = created.json()["id"]
    assert created.json()["tags"] == ["api"]

    assert client.post("/articles", json={"title": "接口"}).status_code == 409

    read = client.get(f"/articles/{article_id}")
    assert read.status_code == 200
    assert read.json()["title"] == "接口"

    listing = client.get("/articles", params={"page": 1, "size": 10})
    assert listing.status_code == 200
    body = listing.json()
    assert body["total"] == 1 and body["items"][0]["id"] == article_id

    updated = client.put(f"/articles/{article_id}", json={"content": "新内容"})
    assert updated.status_code == 200 and updated.json()["content"] == "新内容"

    assert client.get("/articles/999").status_code == 404
    assert client.delete(f"/articles/{article_id}").status_code == 204
    assert client.get(f"/articles/{article_id}").status_code == 404


def test_http_validation_errors(client):
    assert client.post("/articles", json={"title": ""}).status_code == 422
    assert client.post("/articles", json={"content": "没有标题"}).status_code == 422
    assert client.get("/articles", params={"page": 0}).status_code == 422
