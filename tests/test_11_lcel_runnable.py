"""第 11 章测试：LCEL 组合、并行、分支、降级、重试、批量、异步、config。"""

from __future__ import annotations

import asyncio

import pytest

pytest.importorskip("langchain_core")

from langchain_core.messages import AIMessage  # noqa: E402
from langchain_core.runnables import RunnableLambda  # noqa: E402

from learnkit import load  # noqa: E402
from learnkit.lc_fakes import ScriptedChatModel  # noqa: E402

m = load("11_lcel_runnable")


def echo_system_model() -> ScriptedChatModel:
    """把 system 提示词原样回显，方便判断走了哪条分支。"""
    return ScriptedChatModel(responder=lambda messages: AIMessage(content=str(messages[0].content)))


def test_build_chain_invoke_batch_stream():
    model = ScriptedChatModel(
        responder=lambda messages: AIMessage(content=f"答:{messages[-1].content}")
    )
    chain = m.build_chain(model)
    assert chain.invoke({"question": "你好"}) == "答:你好"
    assert m.batch_invoke(chain, ["a", "b"]) == ["答:a", "答:b"]
    assert asyncio.run(m.async_invoke(chain, "c")) == "答:c"


def test_parallel_chain_runs_both_branches():
    model = ScriptedChatModel(responses=[AIMessage(content="摘要结果")])
    chain = m.build_parallel_chain(model)
    result = chain.invoke({"question": "帮我总结"})
    assert result == {"answer": "摘要结果", "echo": "帮我总结"}


def test_branch_chain_routes_by_length():
    assert m.route_by_length({"question": "短"}) == "short"
    assert m.route_by_length({"question": "这是一个很长很长的问题"}) == "long"
    model = echo_system_model()
    chain = m.build_branch_chain(model)
    assert chain.invoke({"question": "短问题"}) == "SHORT"
    assert chain.invoke({"question": "这是一个很长很长的问题"}) == "LONG"


def test_format_docs_and_rag_chain():
    from langchain_core.documents import Document

    docs = [
        Document(page_content="郑州是河南省会", metadata={"source": "a.md"}),
        Document(page_content="开封是古都", metadata={"source": "b.md"}),
    ]
    assert m.format_docs(docs) == "[a.md] 郑州是河南省会\n\n[b.md] 开封是古都"

    retriever = RunnableLambda(lambda question: [docs[0]])
    model = ScriptedChatModel(
        responder=lambda messages: AIMessage(
            content="命中" if "郑州" in messages[-1].content else "未命中"
        )
    )
    chain = m.build_rag_chain(model, retriever)
    assert chain.invoke("郑州是哪里") == "命中"


def test_fallback_chain_switches_on_error():
    def boom(_: str) -> str:
        raise RuntimeError("主链路挂了")

    primary = RunnableLambda(boom)
    fallback = RunnableLambda(lambda text: f"降级:{text}")
    chain = m.with_fallback(primary, fallback)
    assert chain.invoke("hello") == "降级:hello"


def test_retrying_runnable_retries_then_succeeds():
    state = {"calls": 0}

    def flaky(value: int) -> int:
        state["calls"] += 1
        if state["calls"] < 3:
            raise ValueError("再试一次")
        return value * 10

    runnable = m.retrying(flaky, attempts=3)
    assert runnable.invoke(4) == 40
    assert state["calls"] == 3


def test_tagged_run_passes_config():
    runnable = RunnableLambda(lambda value: value + 1)
    result, tags = m.tagged_run(runnable, 1, "my-tag")
    assert result == 2
    assert tags == ["my-tag"]
