"""第 11 章参考实现。"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from operator import itemgetter
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import (
    Runnable,
    RunnableBranch,
    RunnableLambda,
    RunnableParallel,
    RunnablePassthrough,
)


def build_chain(model: BaseChatModel) -> Runnable:
    prompt = ChatPromptTemplate.from_messages([("human", "{question}")])
    return prompt | model | StrOutputParser()


def build_parallel_chain(model: BaseChatModel) -> Runnable:
    prompt = ChatPromptTemplate.from_messages([("human", "{question}")])
    return RunnableParallel(
        answer=prompt | model | StrOutputParser(),
        echo=itemgetter("question"),
    )


def route_by_length(payload: dict[str, Any]) -> str:
    return "long" if len(payload.get("question", "")) > 10 else "short"


def build_branch_chain(model: BaseChatModel) -> Runnable:
    long_chain = (
        ChatPromptTemplate.from_messages([("system", "LONG"), ("human", "{question}")])
        | model
        | StrOutputParser()
    )
    short_chain = (
        ChatPromptTemplate.from_messages([("system", "SHORT"), ("human", "{question}")])
        | model
        | StrOutputParser()
    )
    return RunnableBranch(
        (lambda payload: route_by_length(payload) == "long", long_chain),
        short_chain,
    )


def format_docs(docs: Sequence[Any]) -> str:
    parts = []
    for doc in docs:
        source = getattr(doc, "metadata", {}).get("source", "unknown")
        content = getattr(doc, "page_content", str(doc))
        parts.append(f"[{source}] {content}")
    return "\n\n".join(parts)


def build_rag_chain(model: BaseChatModel, retriever: Runnable) -> Runnable:
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "只能依据下面的资料回答，资料没有就说不知道。"),
            ("human", "资料：\n{context}\n\n问题：{question}"),
        ]
    )
    return (
        RunnableParallel(context=retriever | RunnableLambda(format_docs), question=RunnablePassthrough())
        | prompt
        | model
        | StrOutputParser()
    )


def with_fallback(primary: Runnable, fallback: Runnable) -> Runnable:
    return primary.with_fallbacks([fallback])


def retrying(fn: Callable[[Any], Any], attempts: int = 3) -> Runnable:
    return RunnableLambda(fn).with_retry(stop_after_attempt=attempts, wait_exponential_jitter=False)


def batch_invoke(chain: Runnable, questions: Sequence[str]) -> list[str]:
    return chain.batch([{"question": question} for question in questions])


async def async_invoke(chain: Runnable, question: str) -> str:
    return await chain.ainvoke({"question": question})


def tagged_run(runnable: Runnable, value: Any, tag: str) -> tuple[Any, list[str]]:
    captured: dict[str, list[str]] = {"tags": []}

    def observe(payload: Any, config: Any) -> Any:
        captured["tags"] = list(config.get("tags", []))
        return runnable.invoke(payload)

    result = RunnableLambda(observe).invoke(value, config={"tags": [tag]})
    return result, captured["tags"]
