"""第 12 章测试：切分、向量库、检索、去重、端到端问答。"""

from __future__ import annotations

import asyncio

import pytest

pytest.importorskip("langchain_core")
pytest.importorskip("langchain_text_splitters")

from langchain_core.messages import AIMessage  # noqa: E402

from learnkit import load  # noqa: E402
from learnkit.lc_fakes import ScriptedChatModel  # noqa: E402

m = load("12_rag")

DOCS = {
    "zz.md": "郑州是河南省省会，地处中原，交通枢纽地位突出。郑州有黄河和嵩山。",
    "kf.md": "开封是八朝古都，以清明上河园和灌汤包闻名。开封离郑州很近。",
    "py.md": "Python 的 GIL 让同一进程内多个线程无法并行执行字节码，CPU 密集任务应该用多进程。",
}


def test_load_and_split_keep_metadata():
    documents = m.load_texts(DOCS)
    assert len(documents) == 3
    assert documents[0].metadata["source"] == "zz.md"

    chunks = m.split_documents(documents, chunk_size=20, chunk_overlap=5)
    assert len(chunks) > len(documents), "长文本应该被切成多块"
    assert all("source" in chunk.metadata for chunk in chunks)
    assert [chunk.metadata["chunk_id"] for chunk in chunks] == list(range(len(chunks)))


def test_similarity_search_hits_expected_source():
    store = m.build_vectorstore(m.split_documents(m.load_texts(DOCS), chunk_size=60, chunk_overlap=10))
    results = m.retrieve(store, "开封 清明上河园 灌汤包", k=1)
    assert results[0].metadata["source"] == "kf.md"

    results2 = m.retrieve(store, "GIL 多进程 字节码", k=2)
    assert "py.md" in {doc.metadata["source"] for doc in results2}


def test_hash_embeddings_are_deterministic_and_normalized():
    embeddings = m.make_embeddings(size=32)
    first = embeddings.embed_query("郑州 交通枢纽")
    second = embeddings.embed_query("郑州 交通枢纽")
    assert first == second, "同一个词必须在同一维度"
    assert len(first) == 32
    assert sum(value * value for value in first) == pytest.approx(1.0)
    unrelated = embeddings.embed_query("完全无关的内容")
    assert first != unrelated


def test_retriever_and_format_docs():
    store = m.build_vectorstore(m.split_documents(m.load_texts(DOCS)))
    retriever = m.build_retriever(store, k=2)
    documents = retriever.invoke("郑州 嵩山")
    assert len(documents) == 2
    text = m.format_docs(documents)
    assert text.startswith("[")
    assert "#" in text and "郑州" in text


def test_dedupe_documents_keeps_first():
    documents = m.load_texts(DOCS)
    duplicated = [documents[0], documents[1], documents[0]]
    assert [doc.metadata["source"] for doc in m.dedupe_documents(duplicated)] == ["zz.md", "kf.md"]


def test_end_to_end_rag_passes_context_to_model():
    store = m.build_vectorstore(m.split_documents(m.load_texts(DOCS)))
    retriever = m.build_retriever(store, k=1)

    def responder(messages):
        prompt = str(messages[-1].content)
        if "郑州" in prompt and "资料" in prompt:
            return AIMessage(content="根据资料：郑州是河南省省会。")
        return AIMessage(content="不知道")

    model = ScriptedChatModel(responder=responder)
    answer = asyncio.run(m.answer_question(model, retriever, "郑州是哪里"))
    assert answer == "根据资料：郑州是河南省省会。"
    assert "zz.md" in str(model.seen_messages[0][-1].content)
