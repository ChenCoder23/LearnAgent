"""第 8 章参考实现：分层后端。"""

from __future__ import annotations

from collections.abc import Generator, Sequence
from contextlib import contextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import DateTime, Engine, String, Text, create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


def split_tags(raw: str) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for part in raw.split(","):
        tag = part.strip()
        if tag and tag not in seen:
            seen.add(tag)
            result.append(tag)
    return result


def join_tags(tags: Sequence[str]) -> str:
    return ",".join(split_tags(",".join(tags)))


class Base(DeclarativeBase):
    pass


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    content: Mapped[str] = mapped_column(Text, default="")
    author: Mapped[str] = mapped_column(String(50), default="anonymous")
    tags: Mapped[str] = mapped_column(String(200), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


def make_engine(url: str = "sqlite+pysqlite:///./learn_articles.db", echo: bool = False) -> Engine:
    options: dict[str, object] = {"echo": echo}
    if url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **options)  # type: ignore[arg-type]


def init_db(engine: Engine) -> None:
    Base.metadata.create_all(engine)


@contextmanager
def session_scope(factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


class ArticleCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = ""
    author: str = Field(default="anonymous", max_length=50)
    tags: list[str] = Field(default_factory=list, max_length=10)


class ArticleUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = None
    tags: list[str] | None = None


class ArticleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    author: str
    tags: list[str]
    created_at: datetime


class PageOut(BaseModel):
    items: list[ArticleOut]
    total: int
    page: int
    size: int


class NotFoundError(Exception):
    pass


class ConflictError(Exception):
    pass


def to_out(article: Article) -> ArticleOut:
    return ArticleOut(
        id=article.id,
        title=article.title,
        content=article.content,
        author=article.author,
        tags=split_tags(article.tags),
        created_at=article.created_at,
    )


class ArticleRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, article: Article) -> Article:
        self.session.add(article)
        self.session.flush()
        return article

    def get(self, article_id: int) -> Article | None:
        return self.session.get(Article, article_id)

    def find_by_title(self, title: str) -> Article | None:
        return self.session.scalars(select(Article).where(Article.title == title)).first()

    def list(self, *, offset: int, limit: int, keyword: str | None = None) -> list[Article]:
        statement = select(Article).order_by(Article.id).offset(offset).limit(limit)
        if keyword:
            statement = statement.where(Article.title.contains(keyword))
        return list(self.session.scalars(statement))

    def count(self, keyword: str | None = None) -> int:
        statement = select(func.count()).select_from(Article)
        if keyword:
            statement = statement.where(Article.title.contains(keyword))
        return int(self.session.scalar(statement) or 0)

    def delete(self, article: Article) -> None:
        self.session.delete(article)


class SimpleCache:
    def __init__(self) -> None:
        self._store: dict[str, ArticleOut] = {}
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> ArticleOut | None:
        value = self._store.get(key)
        if value is None:
            self.misses += 1
        else:
            self.hits += 1
        return value

    def set(self, key: str, value: ArticleOut) -> None:
        self._store[key] = value

    def delete(self, key: str) -> None:
        self._store.pop(key, None)


def article_cache_key(article_id: int) -> str:
    return f"article:{article_id}"


class ArticleService:
    def __init__(self, factory: sessionmaker[Session], cache: SimpleCache | None = None) -> None:
        self.factory = factory
        self.cache = cache if cache is not None else SimpleCache()

    def create(self, payload: ArticleCreate) -> ArticleOut:
        with session_scope(self.factory) as session:
            repo = ArticleRepository(session)
            if repo.find_by_title(payload.title) is not None:
                raise ConflictError(f"标题已存在: {payload.title}")
            article = Article(
                title=payload.title,
                content=payload.content,
                author=payload.author,
                tags=join_tags(payload.tags),
            )
            repo.add(article)
            return to_out(article)

    def get(self, article_id: int) -> ArticleOut:
        key = article_cache_key(article_id)
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        with session_scope(self.factory) as session:
            article = ArticleRepository(session).get(article_id)
            if article is None:
                raise NotFoundError(f"文章不存在: {article_id}")
            result = to_out(article)
        self.cache.set(key, result)
        return result

    def list(self, *, page: int = 1, size: int = 10, keyword: str | None = None) -> PageOut:
        if page < 1:
            raise ValueError("page 必须 >= 1")
        if not 1 <= size <= 100:
            raise ValueError("size 必须在 1..100 之间")
        with session_scope(self.factory) as session:
            repo = ArticleRepository(session)
            total = repo.count(keyword)
            items = [
                to_out(article)
                for article in repo.list(offset=(page - 1) * size, limit=size, keyword=keyword)
            ]
        return PageOut(items=items, total=total, page=page, size=size)

    def update(self, article_id: int, payload: ArticleUpdate) -> ArticleOut:
        with session_scope(self.factory) as session:
            repo = ArticleRepository(session)
            article = repo.get(article_id)
            if article is None:
                raise NotFoundError(f"文章不存在: {article_id}")
            if payload.title is not None and payload.title != article.title:
                existing = repo.find_by_title(payload.title)
                if existing is not None and existing.id != article_id:
                    raise ConflictError(f"标题已存在: {payload.title}")
                article.title = payload.title
            if payload.content is not None:
                article.content = payload.content
            if payload.tags is not None:
                article.tags = join_tags(payload.tags)
            session.flush()
            result = to_out(article)
        self.cache.delete(article_cache_key(article_id))
        return result

    def delete(self, article_id: int) -> None:
        with session_scope(self.factory) as session:
            repo = ArticleRepository(session)
            article = repo.get(article_id)
            if article is None:
                raise NotFoundError(f"文章不存在: {article_id}")
            repo.delete(article)
        self.cache.delete(article_cache_key(article_id))


def create_app(engine: Engine, cache: SimpleCache | None = None) -> FastAPI:
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    service = ArticleService(factory, cache)

    app = FastAPI(title="learnAgent articles", version="0.1.0")

    def get_service() -> ArticleService:
        return service

    @app.post("/articles", response_model=ArticleOut, status_code=201)
    def create_article(
        payload: ArticleCreate, svc: ArticleService = Depends(get_service)
    ) -> ArticleOut:
        try:
            return svc.create(payload)
        except ConflictError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    @app.get("/articles", response_model=PageOut)
    def list_articles(
        page: int = Query(default=1, ge=1),
        size: int = Query(default=10, ge=1, le=100),
        keyword: str | None = Query(default=None),
        svc: ArticleService = Depends(get_service),
    ) -> PageOut:
        try:
            return svc.list(page=page, size=size, keyword=keyword)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

    @app.get("/articles/{article_id}", response_model=ArticleOut)
    def read_article(
        article_id: int, svc: ArticleService = Depends(get_service)
    ) -> ArticleOut:
        try:
            return svc.get(article_id)
        except NotFoundError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.put("/articles/{article_id}", response_model=ArticleOut)
    def update_article(
        article_id: int,
        payload: ArticleUpdate,
        svc: ArticleService = Depends(get_service),
    ) -> ArticleOut:
        try:
            return svc.update(article_id, payload)
        except NotFoundError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except ConflictError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    @app.delete("/articles/{article_id}", status_code=204)
    def delete_article(article_id: int, svc: ArticleService = Depends(get_service)) -> None:
        try:
            svc.delete(article_id)
        except NotFoundError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    return app
