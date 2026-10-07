"""第 15 章参考实现。"""

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
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


def split_text(text: str, chunk_size: int, overlap: int = 0) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size 必须大于 0")
    if overlap >= chunk_size:
        raise ValueError("overlap 必须小于 chunk_size")

    chunks: list[str] = []
    for paragraph in [item.strip() for item in re.split(r"\n\s*\n", text) if item.strip()]:
        if len(paragraph) <= chunk_size:
            chunks.append(paragraph)
            continue
        start = 0
        while start < len(paragraph):
            chunks.append(paragraph[start : start + chunk_size])
            if start + chunk_size >= len(paragraph):
                break
            start += chunk_size - overlap
    return chunks


def split_documents(
    documents: list[Document], chunk_size: int, overlap: int = 0
) -> list[Document]:
    result: list[Document] = []
    for document in documents:
        for piece in split_text(document.content, chunk_size, overlap):
            result.append(
                Document(content=piece, metadata={**document.metadata, "chunk_id": len(result)})
            )
    return result


class HashEmbeddings:
    def __init__(self, size: int = 64) -> None:
        self.size = size

    def _tokenize(self, text: str) -> list[str]:
        tokens = re.findall(r"[a-z0-9]+", text.lower())
        compact = re.sub(r"\s+", "", text)
        tokens.extend(compact[i : i + 2] for i in range(len(compact) - 1))
        return tokens

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.size
        for token in self._tokenize(text):
            digest = hashlib.md5(token.encode("utf-8")).hexdigest()
            vector[int(digest, 16) % self.size] += 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self.embed(text)


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        return 0.0
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


class VectorStore:
    def __init__(self, embeddings: HashEmbeddings) -> None:
        self.embeddings = embeddings
        self.documents: list[Document] = []
        self.vectors: list[list[float]] = []

    def add_documents(self, documents: list[Document]) -> None:
        texts = [document.content for document in documents]
        self.vectors.extend(self.embeddings.embed_documents(texts))
        self.documents.extend(documents)

    def similarity_search(self, query: str, k: int = 2) -> list[Document]:
        if not self.documents:
            return []
        query_vector = self.embeddings.embed_query(query)
        scored = [
            (cosine_similarity(query_vector, vector), index)
            for index, vector in enumerate(self.vectors)
        ]
        scored.sort(key=lambda item: (-item[0], item[1]))
        return [self.documents[index] for _score, index in scored[:k]]

    def as_retriever(self, k: int = 2) -> Any:
        return core.RunnableLambda(lambda question: self.similarity_search(question, k))


def format_documents(documents: list[Document]) -> str:
    parts = []
    for document in documents:
        source = document.metadata.get("source", "unknown")
        chunk_id = document.metadata.get("chunk_id", "-")
        parts.append(f"[{source}#{chunk_id}] {document.content}")
    return "\n\n".join(parts)


def build_rag_chain(model: Any, store: VectorStore, k: int = 2) -> Any:
    retriever = store.as_retriever(k)
    prompt = core.ChatPromptTemplate.from_messages(
        [
            ("system", "只能依据给定资料回答；资料不足就直接说“不知道”。"),
            ("human", "资料：\n{context}\n\n问题：{question}"),
        ]
    )
    prepare = core.RunnableParallel(
        {
            "context": core.RunnableLambda(
                lambda payload, config=None: format_documents(
                    retriever.invoke(payload.get("question", ""))
                )
            ),
            "question": core.RunnableLambda(lambda payload: payload.get("question", "")),
        }
    )
    return prepare | prompt | model | core.StrOutputParser()
