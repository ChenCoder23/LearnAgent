"""第 15 章测试：手写切分、向量、检索与 RAG 链。"""

from __future__ import annotations

import pytest

from learnkit import load

m = load("15_mini_rag")
core = load("14_mini_core")

TEXTS = [
    m.Document(content="郑州是河南省省会，交通枢纽。\n\n郑州有嵩山和黄河。", metadata={"source": "zz.md"}),
    m.Document(content="开封是八朝古都，以清明上河园和灌汤包闻名。", metadata={"source": "kf.md"}),
]


def test_split_text_respects_size_and_overlap():
    chunks = m.split_text("A" * 25, chunk_size=10, overlap=3)
    assert all(len(chunk) <= 10 for chunk in chunks)
    assert len(chunks) >= 3
    assert chunks[1][:3] == chunks[0][-3:], "相邻块要有重叠"
    with pytest.raises(ValueError):
        m.split_text("x", chunk_size=0)
    with pytest.raises(ValueError):
        m.split_text("x" * 10, chunk_size=5, overlap=5)


def test_split_documents_adds_chunk_ids():
    chunks = m.split_documents(TEXTS, chunk_size=12, overlap=2)
    assert len(chunks) > len(TEXTS)
    assert [chunk.metadata["chunk_id"] for chunk in chunks] == list(range(len(chunks)))
    assert {chunk.metadata["source"] for chunk in chunks} == {"zz.md", "kf.md"}


def test_embeddings_and_cosine():
    embeddings = m.HashEmbeddings(size=32)
    left = embeddings.embed_query("郑州 交通")
    assert left == embeddings.embed_query("郑州 交通")
    assert sum(value * value for value in left) == pytest.approx(1.0)
    assert m.cosine_similarity(left, left) == pytest.approx(1.0)
    assert m.cosine_similarity(left, embeddings.embed_query("完全无关")) < 0.9
    assert m.cosine_similarity([], []) == 0.0


def test_vector_store_retrieval():
    store = m.VectorStore(m.HashEmbeddings(size=64))
    store.add_documents(TEXTS)
    results = store.similarity_search("清明上河园 灌汤包", k=1)
    assert results[0].metadata["source"] == "kf.md"
    assert store.similarity_search("郑州 嵩山", k=1)[0].metadata["source"] == "zz.md"
    assert m.VectorStore(m.HashEmbeddings()).similarity_search("空库", k=1) == []


def test_retriever_is_runnable_and_rag_chain_end_to_end():
    store = m.VectorStore(m.HashEmbeddings(size=64))
    store.add_documents(TEXTS)
    retriever = store.as_retriever(k=1)
    assert isinstance(retriever, core.Runnable)
    assert retriever.invoke("灌汤包")[0].metadata["source"] == "kf.md"

    model = core.FakeChatModel(["开封是八朝古都。"])
    chain = m.build_rag_chain(model, store, k=1)
    answer = chain.invoke({"question": "开封以什么闻名"})
    assert answer == "开封是八朝古都。"
    prompt_text = model.seen[0][-1].content
    assert "kf.md" in prompt_text and "资料" in prompt_text


def test_format_documents():
    text = m.format_documents(m.split_documents(TEXTS[:1], chunk_size=100))
    assert text.startswith("[zz.md#0]")
