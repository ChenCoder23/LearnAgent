"""第 15 章：手写 mini RAG —— Document / 切分 / 向量 / 向量库 / 检索链

依赖：先完成第 14 章（本章复用它的 Runnable、ChatPromptTemplate、StrOutputParser）。

第 12 章你已经用现成组件跑通过 RAG；这一章要自己造出来。造完你会明白：

- 向量检索 = 余弦相似度排序，没什么魔法；
- “切分策略”和“embedding 质量”才是 RAG 效果的关键，模型只负责最后一句话；
- 检索器本身就是一个 Runnable，所以能直接 ``|`` 到链里。
"""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass, field
from typing import Any

from learnkit import load

core = load("14_mini_core")


@dataclass
class Document:
    """文档片段：内容和元数据（来源、位置、chunk 序号……）。"""

    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


def split_text(text: str, chunk_size: int, overlap: int = 0) -> list[str]:
    """按“先段落、再硬切”的策略切分文本：

    1. 先按空行切成段落；
    2. 段落超过 ``chunk_size`` 就硬切成多块；
    3. 相邻块之间保留 ``overlap`` 个字符的重叠（避免语义被切断）。

    ``chunk_size <= 0`` 抛 ``ValueError``；``overlap >= chunk_size`` 抛 ``ValueError``。
    """
    raise NotImplementedError("TODO")


def split_documents(documents: list[Document], chunk_size: int, overlap: int = 0) -> list[Document]:
    """切分文档并补上 ``chunk_id``（从 0 开始，全局递增），保留原有 metadata。"""
    raise NotImplementedError("TODO")


class HashEmbeddings:
    """字符 bigram + md5 哈希的确定性向量器（第 12 章写过，这次不看答案重写一遍）。

    调用方约定：``embed_documents(texts)`` / ``embed_query(text)`` 返回 L2 归一化后的向量。
    """

    def __init__(self, size: int = 64) -> None:
        raise NotImplementedError("TODO")

    def _tokenize(self, text: str) -> list[str]:
        raise NotImplementedError("TODO")

    def embed(self, text: str) -> list[float]:
        raise NotImplementedError("TODO")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("TODO")

    def embed_query(self, text: str) -> list[float]:
        raise NotImplementedError("TODO")


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """余弦相似度。向量已归一化时它就是点积；长度为 0 时返回 0.0。"""
    raise NotImplementedError("TODO")


class VectorStore:
    """最简向量库：把 (文档, 向量) 存在内存里，检索时算相似度排序。"""

    def __init__(self, embeddings: HashEmbeddings) -> None:
        raise NotImplementedError("TODO")

    def add_documents(self, documents: list[Document]) -> None:
        raise NotImplementedError("TODO: 批量 embed 后存起来")

    def similarity_search(self, query: str, k: int = 2) -> list[Document]:
        raise NotImplementedError("TODO: 按相似度降序取前 k 条")

    def as_retriever(self, k: int = 2) -> Any:
        """返回一个 Runnable：输入问题字符串，输出 ``list[Document]``。

        提示：``core.RunnableLambda(lambda question: self.similarity_search(question, k))``
        """
        raise NotImplementedError("TODO")


def format_documents(documents: list[Document]) -> str:
    """拼成上下文：``[source#chunk_id] 内容``，两条之间空一行。"""
    raise NotImplementedError("TODO")


def build_rag_chain(model: Any, store: VectorStore, k: int = 2) -> Any:
    """用第 14 章的原语搭一条 RAG 链，输入 ``{"question": ...}``，输出字符串。

    结构参考：``RunnableParallel(context=检索并拼接, question=取原问题) | 模板 | 模型 | 解析器``
    """
    raise NotImplementedError("TODO")
