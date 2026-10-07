"""第 11 章：Runnable 与 LCEL —— 把组件连成流水线

LCEL 的核心只有一个符号：``|``。左边的东西输出什么，右边就收到什么。

    提示词模板 | 模型 | 输出解析器

每个 Runnable 都提供同一套方法，这是 LangChain 最值钱的设计：
``invoke`` / ``batch`` / ``stream`` / ``ainvoke`` / ``with_retry`` / ``with_fallbacks``。
学会它，你就获得“换模型、加并发、加重试、加降级”都不用改业务代码的能力。

第三阶段你会亲手实现这套接口，那时你会更清楚它为什么这么设计。
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
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
    """返回 ``prompt | model | StrOutputParser()``。

    - prompt 用 ``ChatPromptTemplate.from_messages``，其中 ``("human", "{question}")``
    - 输入是 ``{"question": "..."}``，输出是字符串
    """
    raise NotImplementedError("TODO")


def build_parallel_chain(model: BaseChatModel) -> Runnable:
    """用 ``RunnableParallel`` 同时算两件事，返回 ``{"answer": 模型答案, "echo": 问题原样}``。

    ``echo`` 用 ``RunnablePassthrough()`` 从输入里取 ``question``（提示：``itemgetter`` 或 lambda）。
    """
    raise NotImplementedError("TODO")


def route_by_length(payload: dict[str, Any]) -> str:
    """路由函数：``question`` 长度 > 10 返回 ``"long"``，否则 ``"short"``。"""
    raise NotImplementedError("TODO")


def build_branch_chain(model: BaseChatModel) -> Runnable:
    """用 ``RunnableBranch`` 做条件分支：

    - long 分支：system 写 ``"LONG"``
    - short 分支：system 写 ``"SHORT"``
    两条分支都是 ``prompt | model | StrOutputParser()``。
    """
    raise NotImplementedError("TODO")


def format_docs(docs: Sequence[Any]) -> str:
    """把检索结果拼成上下文文本：每条形如 ``[source] content``，用两个换行分隔。"""
    raise NotImplementedError("TODO")


def build_rag_chain(model: BaseChatModel, retriever: Runnable) -> Runnable:
    """经典 RAG 链：

        {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt | model | StrOutputParser()

    prompt 里 human 模板包含 ``{context}`` 和 ``{question}``。
    """
    raise NotImplementedError("TODO")


def with_fallback(primary: Runnable, fallback: Runnable) -> Runnable:
    """主链失败时自动降级到备用链：``primary.with_fallbacks([fallback])``。"""
    raise NotImplementedError("TODO")


def retrying(fn: Callable[[Any], Any], attempts: int = 3) -> Runnable:
    """把普通函数包成可重试的 Runnable（``with_retry``），测试里要看到它真的重试了。"""
    raise NotImplementedError("TODO: wait_exponential_jitter=False 让测试跑得快")


def batch_invoke(chain: Runnable, questions: Sequence[str]) -> list[str]:
    """批量执行（``chain.batch``），保持输入顺序。"""
    raise NotImplementedError("TODO")


async def async_invoke(chain: Runnable, question: str) -> str:
    """异步执行（``chain.ainvoke``）。"""
    raise NotImplementedError("TODO")


def tagged_run(runnable: Runnable, value: Any, tag: str) -> tuple[Any, list[str]]:
    """带配置执行：``runnable.invoke(value, config={"tags": [tag]})``，
    返回 (结果, 这次执行实际收到的 tags)。

    提示：把 runnable 包成 ``RunnableLambda(lambda value, config: ...)`` 才能在函数里拿到 config。
    """
    raise NotImplementedError("TODO")
