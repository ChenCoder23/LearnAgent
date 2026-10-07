"""第 10 章：LangChain 起步 —— 消息、Prompt 模板、输出解析

三件套先记牢：**消息（Messages）→ 模板（Prompt）→ 解析（OutputParser）**。

这一章的所有练习都能离线跑：测试用 ``learnkit.lc_fakes.ScriptedChatModel`` 当模型，
它按剧本返回消息，还能绑定工具（第 13 章会用上）。

想调真实模型时看同目录 ``real_api_demo.py``（需要 OPENAI_API_KEY）。
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


def build_messages(
    system: str, history: Sequence[BaseMessage] | None = None, user: str = ""
) -> list[BaseMessage]:
    """构造消息列表：SystemMessage + history + HumanMessage。

    规则：``system`` 为空则不添加；``user`` 为空则不添加最后一条 HumanMessage。
    """
    raise NotImplementedError("TODO: 注意 history 可能为 None，不要直接 +")


def build_prompt_template(system: str) -> ChatPromptTemplate:
    """返回一个 ChatPromptTemplate，结构为：

    ``("system", system)`` + ``MessagesPlaceholder("history", optional=True)`` + ``("human", "{question}")``
    """
    raise NotImplementedError("TODO")


def render_prompt(
    template: ChatPromptTemplate, question: str, history: Sequence[BaseMessage] | None = None
) -> list[BaseMessage]:
    """把模板和数据渲染成真正的消息列表（``template.invoke`` 或 ``format_messages``）。"""
    raise NotImplementedError("TODO")


def ask_model(model: BaseChatModel, question: str, system: str = "你是严谨的中文助教") -> str:
    """把 system + question 交给模型，返回纯文本答案（用 ``StrOutputParser``）。"""
    raise NotImplementedError("TODO")


def stream_tokens(model: BaseChatModel, question: str) -> list[str]:
    """用 ``model.stream`` 收集所有 chunk 的文本，返回列表。

    注意：返回的是**增量片段**，拼接起来才等于完整答案。
    """
    raise NotImplementedError("TODO")


def extract_usage(message: BaseMessage) -> dict[str, int]:
    """从 AIMessage 里取 token 用量。

    没有 ``usage_metadata``（很多本地模型 / 假模型都没有）时返回全 0 的默认值，
    字段为 ``input_tokens`` / ``output_tokens`` / ``total_tokens``。
    """
    raise NotImplementedError("TODO: 用 getattr(message, 'usage_metadata', None)")


def parse_article_json(raw: str) -> dict[str, Any]:
    """把模型输出的 JSON 字符串解析成字典，并做最小校验：

    - 必须有非空字符串 ``title``
    - ``tags`` 缺省时补 ``[]``；给了必须是字符串列表
    用 ``JsonOutputParser().parse(raw)`` 解析（它会容忍 ```json 代码块包裹）。
    """
    raise NotImplementedError("TODO")


def trim_history(messages: Sequence[BaseMessage], max_chars: int) -> list[BaseMessage]:
    """按字符预算裁剪上下文（真实项目里必须做的事，否则迟早撞上 token 上限）。

    规则：

    - 所有 SystemMessage 永远保留
    - 其余消息从**最新**往前累加，直到再加一条就超过 ``max_chars`` 为止
    - 至少保留最后一条消息（哪怕它自己就超预算）
    - 返回的消息顺序要与原来一致
    """
    raise NotImplementedError("TODO")


def main() -> None:  # pragma: no cover - 手动运行用
    """手动实践：``uv run python labs/10_llm_prompt_parser/lab.py`` 之前先实现上面的函数。"""
    from learnkit.lc_fakes import ScriptedChatModel

    model = ScriptedChatModel(responses=[AIMessage(content="这是离线假模型的回答")])
    print(ask_model(model, "你好"))
    print(stream_tokens(model, "你好"))


if __name__ == "__main__":  # pragma: no cover
    main()
