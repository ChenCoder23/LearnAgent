"""第 10 章参考实现。"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


def build_messages(
    system: str, history: Sequence[BaseMessage] | None = None, user: str = ""
) -> list[BaseMessage]:
    messages: list[BaseMessage] = []
    if system:
        messages.append(SystemMessage(content=system))
    if history:
        messages.extend(history)
    if user:
        messages.append(HumanMessage(content=user))
    return messages


def build_prompt_template(system: str) -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            ("system", system),
            MessagesPlaceholder("history", optional=True),
            ("human", "{question}"),
        ]
    )


def render_prompt(
    template: ChatPromptTemplate, question: str, history: Sequence[BaseMessage] | None = None
) -> list[BaseMessage]:
    return template.format_messages(question=question, history=list(history or []))


def ask_model(model: BaseChatModel, question: str, system: str = "你是严谨的中文助教") -> str:
    parser = StrOutputParser()
    message = model.invoke(build_messages(system, None, question))
    return parser.invoke(message)


def stream_tokens(model: BaseChatModel, question: str) -> list[str]:
    chunks: list[str] = []
    for chunk in model.stream(build_messages("", None, question)):
        content = chunk.content
        chunks.append(content if isinstance(content, str) else str(content))
    return chunks


def extract_usage(message: BaseMessage) -> dict[str, int]:
    usage = getattr(message, "usage_metadata", None)
    if not usage:
        return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    return {
        "input_tokens": int(usage.get("input_tokens", 0)),
        "output_tokens": int(usage.get("output_tokens", 0)),
        "total_tokens": int(usage.get("total_tokens", 0)),
    }


def parse_article_json(raw: str) -> dict[str, Any]:
    data = JsonOutputParser().parse(raw)
    if not isinstance(data, dict):
        raise ValueError(f"模型返回的不是 JSON 对象: {type(data).__name__}")
    title = data.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("缺少非空 title")
    tags = data.get("tags", [])
    if not isinstance(tags, list) or any(not isinstance(tag, str) for tag in tags):
        raise ValueError("tags 必须是字符串列表")
    return {"title": title.strip(), "tags": tags, "content": str(data.get("content", ""))}


def trim_history(messages: Sequence[BaseMessage], max_chars: int) -> list[BaseMessage]:
    if not messages:
        return []
    system_messages = [m for m in messages if isinstance(m, SystemMessage)]
    others = [m for m in messages if not isinstance(m, SystemMessage)]
    if not others:
        return list(system_messages)

    used = 0
    kept: list[BaseMessage] = []
    for message in reversed(others):
        length = len(str(message.content))
        if kept and used + length > max_chars:
            break
        kept.append(message)
        used += length
    return system_messages + list(reversed(kept))
