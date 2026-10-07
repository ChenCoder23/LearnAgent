"""第 12 章：RAG 检索增强生成（离线可跑）

RAG 的完整链路：

    文档 -> 切分(chunk) -> 向量化(embedding) -> 存入向量库 -> 检索 top-k -> 塞进提示词 -> 模型回答

四个最容易翻车的点，本章都会让你亲手碰到：

1. 切分太碎：语义被切断，检索到也没用；
2. 不保留 metadata：答案给不出来源，无法追溯；
3. 只看相似度：top-k 里混进无关内容，模型被带偏；
4. 不做评估：改了一版切分策略，效果变好还是变差全靠感觉。

本章的 embedding 由**你自己实现**（字符二元组 + md5 哈希成固定维度向量），
所以不花钱、不联网、结果确定。理解了它，你也就理解了“向量检索”到底在算什么；
换真实模型时只要把它替换成 ``OpenAIEmbeddings()``，其余代码一行都不用改。
"""

from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Sequence
from typing import Any

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter


def load_texts(payload: dict[str, str]) -> list[Any]:
    """把 ``{"a.md": "内容"}`` 变成 ``[Document(page_content=..., metadata={"source": "a.md"})]``。

    metadata 决定你以后能不能回答“这句话出自哪个文件”，一定要带上。
    """
    raise NotImplementedError("TODO: from langchain_core.documents import Document")


def split_documents(
    documents: Sequence[Any], chunk_size: int = 120, chunk_overlap: int = 20
) -> list[Any]:
    """用 ``RecursiveCharacterTextSplitter`` 切分：

    - 保留原有 metadata（切分器会自动带上）
    - 给每个 chunk 补一个 ``chunk_id``（从 0 递增）
    """
    raise NotImplementedError("TODO")


class HashEmbeddings(Embeddings):
    """最朴素的“词袋 + 哈希”向量：

    1. 把文本切成 token：英文/数字按词切，中文按相邻两字切（bigram）；
    2. 每个 token 用 ``hashlib.md5`` 取摘要，再对 ``size`` 取模得到维度下标；
    3. 该维度计数 +1，最后做 L2 归一化。

    为什么要用 ``hashlib`` 而不是内置 ``hash()``？因为字符串的内置 hash 每个进程都会加盐变化，
    会导致“同一个词在不同进程落到不同维度”，检索结果不可复现。这是真实踩过的坑。
    """

    def __init__(self, size: int = 64) -> None:
        raise NotImplementedError("TODO")

    def _tokenize(self, text: str) -> list[str]:
        raise NotImplementedError("TODO: 英文小写按 \\w+ 切；中文字符串去掉空白后取相邻两字")

    def _vector(self, text: str) -> list[float]:
        raise NotImplementedError("TODO")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("TODO")

    def embed_query(self, text: str) -> list[float]:
        raise NotImplementedError("TODO")


def make_embeddings(size: int = 64) -> Embeddings:
    """返回上面那个哈希向量器（第 15 章会再实现一次更完整的版本）。"""
    raise NotImplementedError("TODO")


def build_vectorstore(documents: Sequence[Any], embeddings: Any | None = None) -> InMemoryVectorStore:
    """建库并写入文档：``InMemoryVectorStore(embedding=...)`` + ``add_documents``。"""
    raise NotImplementedError("TODO")


def build_retriever(store: InMemoryVectorStore, k: int = 2) -> Any:
    """``store.as_retriever(search_kwargs={"k": k})``。"""
    raise NotImplementedError("TODO")


def retrieve(store: InMemoryVectorStore, query: str, k: int = 2) -> list[Any]:
    """直接相似度检索（``similarity_search``），便于做单测。"""
    raise NotImplementedError("TODO")


def format_docs(documents: Sequence[Any]) -> str:
    """拼上下文：``[source#chunk_id] 内容``，用两个换行分隔。"""
    raise NotImplementedError("TODO")


def dedupe_documents(documents: Sequence[Any]) -> list[Any]:
    """按 ``page_content`` 去重，保持首次出现顺序（检索结果常常重复）。"""
    raise NotImplementedError("TODO")


async def answer_question(model: BaseChatModel, retriever: Any, question: str) -> str:
    """完整问答：检索 -> 拼上下文 -> 回答。

    prompt 要求：system 里明确“只依据资料回答，资料不足就说不知道”；
    human 里带 ``{context}`` 与 ``{question}``。
    """
    raise NotImplementedError("TODO: 可以用 LCEL，也可以直接拼消息后 model.invoke")
