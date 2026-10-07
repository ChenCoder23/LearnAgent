"""第 12 章参考实现。"""

from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Sequence
from typing import Any

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter


def load_texts(payload: dict[str, str]) -> list[Document]:
    return [
        Document(page_content=content, metadata={"source": source})
        for source, content in payload.items()
    ]


def split_documents(
    documents: Sequence[Document], chunk_size: int = 120, chunk_overlap: int = 20
) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    chunks = splitter.split_documents(list(documents))
    for index, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = index
    return chunks


class HashEmbeddings(Embeddings):
    def __init__(self, size: int = 64) -> None:
        self.size = size

    def _tokenize(self, text: str) -> list[str]:
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        compact = re.sub(r"\s+", "", text)
        tokens.extend(compact[i : i + 2] for i in range(len(compact) - 1))
        return tokens

    def _vector(self, text: str) -> list[float]:
        vector = [0.0] * self.size
        for token in self._tokenize(text):
            digest = hashlib.md5(token.encode("utf-8")).hexdigest()
            vector[int(digest, 16) % self.size] += 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vector(text)


def make_embeddings(size: int = 64) -> Embeddings:
    return HashEmbeddings(size=size)


def build_vectorstore(
    documents: Sequence[Document], embeddings: Any | None = None
) -> InMemoryVectorStore:
    store = InMemoryVectorStore(embedding=embeddings or make_embeddings())
    store.add_documents(list(documents))
    return store


def build_retriever(store: InMemoryVectorStore, k: int = 2) -> Any:
    return store.as_retriever(search_kwargs={"k": k})


def retrieve(store: InMemoryVectorStore, query: str, k: int = 2) -> list[Document]:
    return store.similarity_search(query, k=k)


def format_docs(documents: Sequence[Document]) -> str:
    parts = []
    for doc in documents:
        source = doc.metadata.get("source", "unknown")
        chunk_id = doc.metadata.get("chunk_id", "-")
        parts.append(f"[{source}#{chunk_id}] {doc.page_content}")
    return "\n\n".join(parts)


def dedupe_documents(documents: Sequence[Document]) -> list[Document]:
    seen: set[str] = set()
    result: list[Document] = []
    for doc in documents:
        if doc.page_content not in seen:
            seen.add(doc.page_content)
            result.append(doc)
    return result


async def answer_question(model: BaseChatModel, retriever: Any, question: str) -> str:
    documents = dedupe_documents(list(retriever.invoke(question)))
    context = format_docs(documents) if documents else "（没有检索到资料）"
    messages = [
        SystemMessage(content="只能依据给定资料回答；资料不足就直接说“不知道”。"),
        HumanMessage(content=f"资料：\n{context}\n\n问题：{question}"),
    ]
    response = await model.ainvoke(messages)
    content = response.content
    return content if isinstance(content, str) else str(content)
