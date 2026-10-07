"""第 8 章：用 FastAPI + SQLAlchemy 2.0 写一个分层后端

这一章是阶段一的验收关卡：做完它，你就具备“独立写 Python 后端接口（含数据库）”的能力。

分层（每一层只做一件事）：

    HTTP 路由  ->  负责解析请求、返回状态码，不写业务规则
    服务层     ->  业务规则（唯一性、缓存、事务边界），返回 DTO
    仓储层     ->  只跟数据库打交道（CRUD + 查询条件）
    模型/模式  ->  ORM Model 负责“表长什么样”，Pydantic Schema 负责“接口长什么样”

为什么必须分层？因为未来加缓存、加权限、换数据库、写测试都只在某一层动，不会牵连全部代码。

依赖：uv sync --extra stage1
"""

from __future__ import annotations

from collections.abc import Generator, Iterator, Sequence
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import DateTime, Engine, String, Text, create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


# --------------------------------------------------------------------------------------
# 1. 小工具：标签的序列化
# --------------------------------------------------------------------------------------
def split_tags(raw: str) -> list[str]:
    """把数据库里的 ``"python, fastapi ,backend"`` 变成 ``["python", "fastapi", "backend"]``。

    要求：去空白、丢弃空串、去重且保持首次出现顺序。空字符串返回 ``[]``。
    """
    raise NotImplementedError("TODO: 用第 1 章的保序去重思路")


def join_tags(tags: Sequence[str]) -> str:
    """``["python", "fastapi"]`` -> ``"python,fastapi"``（同样去空白、去重、保序）。"""
    raise NotImplementedError("TODO")


# --------------------------------------------------------------------------------------
# 2. 数据库：Engine / Session / ORM 模型
# --------------------------------------------------------------------------------------
class Base(DeclarativeBase):
    """所有 ORM 模型的基类（SQLAlchemy 2.0 风格）。"""


class Article(Base):
    """文章表。

    字段：

    - ``id``：主键，自增
    - ``title``：字符串 200，唯一 + 索引（唯一约束就是“业务上的唯一性”在数据库的兜底）
    - ``content``：Text
    - ``author``：字符串 50，默认 ``"anonymous"``
    - ``tags``：用逗号拼接的字符串存（教学简化版；真实项目可用 JSON 列或关联表）
    - ``created_at``：UTC 时间，默认取当前时间
    """

    __tablename__ = "articles"

    # 主键先给出（否则 SQLAlchemy 在建映射时就会报错，所有测试都跑不起来）
    id: Mapped[int] = mapped_column(primary_key=True)
    # TODO: 补全 title / content / author / tags / created_at 五列，
    #       注意 title 需要 String(200) + unique=True + index=True


def make_engine(url: str = "sqlite+pysqlite:///./learn_articles.db", echo: bool = False) -> Engine:
    """创建 Engine。

    SQLite 需要 ``connect_args={"check_same_thread": False}``，否则 FastAPI 的线程池会报错。
    其他数据库不要传这个参数。
    """
    raise NotImplementedError("TODO")


def init_db(engine: Engine) -> None:
    """建表：``Base.metadata.create_all(engine)``。

    生产环境应该用 Alembic 迁移而不是这个函数，这里先用它让项目跑起来。
    """
    raise NotImplementedError("TODO")


@contextmanager
def session_scope(factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    """事务边界：正常结束 commit，出异常 rollback，最后一定 close。

    这就是第 4 章 ``transaction`` 的真实用法。
    """
    raise NotImplementedError("TODO")


# --------------------------------------------------------------------------------------
# 3. 接口模式（Pydantic Schema）
# --------------------------------------------------------------------------------------
class ArticleCreate(BaseModel):
    """创建文章的请求体：``title`` 1..200 字符，``content`` 可以为空，``tags`` 最多 10 个。"""

    title: str = Field(min_length=1, max_length=200)
    content: str = ""
    author: str = Field(default="anonymous", max_length=50)
    tags: list[str] = Field(default_factory=list, max_length=10)


class ArticleUpdate(BaseModel):
    """更新请求体：所有字段可选，只更新传了的字段。"""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = None
    tags: list[str] | None = None


class ArticleOut(BaseModel):
    """返回给客户端的 DTO。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    author: str
    tags: list[str]
    created_at: datetime


class PageOut(BaseModel):
    """分页返回：items + total + page + size。"""

    items: list[ArticleOut]
    total: int
    page: int
    size: int


# --------------------------------------------------------------------------------------
# 4. 异常：业务异常与 HTTP 解耦
# --------------------------------------------------------------------------------------
class NotFoundError(Exception):
    """资源不存在（服务层抛，路由层翻译成 404）。"""


class ConflictError(Exception):
    """唯一性冲突（服务层抛，路由层翻译成 409）。"""


def to_out(article: Article) -> ArticleOut:
    """ORM 对象 -> DTO。这里显式转换，好处是接口字段与表结构可以独立演进。"""
    raise NotImplementedError("TODO: 注意 tags 要用 split_tags 还原成 list")


# --------------------------------------------------------------------------------------
# 5. 仓储层：只跟数据库打交道
# --------------------------------------------------------------------------------------
class ArticleRepository:
    def __init__(self, session: Session) -> None:
        raise NotImplementedError("TODO")

    def add(self, article: Article) -> Article:
        """add + flush（拿到自增 id），不要在这里 commit。"""
        raise NotImplementedError("TODO")

    def get(self, article_id: int) -> Article | None:
        raise NotImplementedError("TODO")

    def find_by_title(self, title: str) -> Article | None:
        raise NotImplementedError("TODO")

    def list(self, *, offset: int, limit: int, keyword: str | None = None) -> list[Article]:
        """按 id 升序返回；``keyword`` 存在时用 ``title LIKE`` 模糊匹配。"""
        raise NotImplementedError("TODO")

    def count(self, keyword: str | None = None) -> int:
        """统计总数（分页要同时返回 total，否则前端画不出页码）。"""
        raise NotImplementedError("TODO")

    def delete(self, article: Article) -> None:
        raise NotImplementedError("TODO")


# --------------------------------------------------------------------------------------
# 6. 缓存：先用最小接口，第 9 章会换成 Redis 并解决三大问题
# --------------------------------------------------------------------------------------
class SimpleCache:
    """进程内缓存（dict 版）。真实项目里换成 Redis，接口是一样的。"""

    def __init__(self) -> None:
        raise NotImplementedError("TODO")

    def get(self, key: str) -> ArticleOut | None:
        raise NotImplementedError("TODO")

    def set(self, key: str, value: ArticleOut) -> None:
        raise NotImplementedError("TODO")

    def delete(self, key: str) -> None:
        raise NotImplementedError("TODO")


def article_cache_key(article_id: int) -> str:
    """统一 key 规范：``"article:42"``。key 命名一定要收口到一个函数里。"""
    raise NotImplementedError("TODO")


# --------------------------------------------------------------------------------------
# 7. 服务层：业务规则 + 事务 + 缓存
# --------------------------------------------------------------------------------------
class ArticleService:
    """构造函数接收 session 工厂与缓存，方便测试时替换。

    缓存策略（Cache-Aside）：

    - 读：先查缓存，命中直接返回；未命中查库，写回缓存
    - 写：先写库并提交，然后**删除**缓存（不是更新缓存，避免并发写导致脏数据）
    """

    def __init__(self, factory: sessionmaker[Session], cache: SimpleCache | None = None) -> None:
        raise NotImplementedError("TODO")

    def create(self, payload: ArticleCreate) -> ArticleOut:
        """创建文章；标题已存在则抛 ``ConflictError``。"""
        raise NotImplementedError("TODO")

    def get(self, article_id: int) -> ArticleOut:
        """按 id 取文章；不存在抛 ``NotFoundError``。命中缓存时不应查库（测试会验证）。"""
        raise NotImplementedError("TODO")

    def list(self, *, page: int = 1, size: int = 10, keyword: str | None = None) -> PageOut:
        """分页查询；``page < 1`` 或 ``size`` 不在 1..100 抛 ``ValueError``。"""
        raise NotImplementedError("TODO")

    def update(self, article_id: int, payload: ArticleUpdate) -> ArticleOut:
        """局部更新；改标题造成冲突抛 ``ConflictError``；更新后删缓存。"""
        raise NotImplementedError("TODO")

    def delete(self, article_id: int) -> None:
        """删除；不存在抛 ``NotFoundError``；删除后删缓存。"""
        raise NotImplementedError("TODO")


# --------------------------------------------------------------------------------------
# 8. 路由层：只做“翻译”
# --------------------------------------------------------------------------------------
def create_app(engine: Engine, cache: SimpleCache | None = None) -> FastAPI:
    """组装 FastAPI 应用。

    要求：

    - ``POST /articles`` -> 201 + ArticleOut
    - ``GET /articles`` -> PageOut（查询参数 page/size/keyword）
    - ``GET /articles/{article_id}`` -> ArticleOut
    - ``PUT /articles/{article_id}`` -> ArticleOut
    - ``DELETE /articles/{article_id}`` -> 204，无响应体
    - ``NotFoundError`` -> 404，``ConflictError`` -> 409，``ValueError`` -> 422
    - 用 ``Depends`` 注入 ``ArticleService``（每个请求一个 session）
    """
    raise NotImplementedError("TODO")
