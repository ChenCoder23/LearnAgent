"""离线可用的假模型 / 假 embedding，供第二阶段练习与测试使用。

为什么要自己写一个假模型？

1. 教学项目必须**不联网、不花钱**也能跑，否则你会在“没 API Key”这件事上卡住。
2. 决定论：同一段脚本每次返回同样的结果，测试才写得出来。
3. LangChain 的 FakeListChatModel 不实现 ``bind_tools``，跑不了 Agent 循环，
   所以这里实现一个能绑定工具的版本。

写完自己的 mini 框架（第三阶段）后，回头对比这个类与 ``langchain_core`` 的
``BaseChatModel``，你会对“抽象基类 + 回调 + 注册表”这套设计有更具体的感受。
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Sequence
from typing import Any

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from pydantic import Field, PrivateAttr


class ScriptedChatModel(BaseChatModel):
    """按剧本返回消息的离线模型，支持 ``bind_tools``。

    两种用法::

        # 1) 固定剧本：第 1 次调用返回 responses[0]，第 2 次返回 responses[1] …
        model = ScriptedChatModel(responses=[AIMessage(content="第一步"), AIMessage(content="第二步")])

        # 2) 用函数动态决定（可以按 messages 内容分支）
        model = ScriptedChatModel(responder=lambda messages: AIMessage(content=str(len(messages))))
    """

    responses: list[BaseMessage] = Field(default_factory=list)
    responder: Callable[[list[BaseMessage]], BaseMessage] | None = None
    bound_tools: list[str] = Field(default_factory=list)
    # 记录每次被调用时看到的完整消息列表，方便测试断言“模型确实看到了工具结果”
    seen_messages: list[list[BaseMessage]] = Field(default_factory=list)
    # 用 list 当计数器：LangChain 每次调用模型都会重新 bind_tools 生成副本，
    # 只有共享同一个可变对象，游标才能跨副本前进（这是个很值得记住的坑）。
    _cursor: list[int] = PrivateAttr(default_factory=lambda: [0])

    @property
    def _llm_type(self) -> str:
        return "scripted-chat-model"

    def bind_tools(self, tools: Sequence[Any], **kwargs: Any) -> ScriptedChatModel:
        """记录工具并返回自身副本。真模型会把这些工具转成 JSON Schema 发给服务端。"""
        names = [getattr(t, "name", None) or getattr(t, "__name__", str(t)) for t in tools]
        for name in names:
            if name not in self.bound_tools:
                self.bound_tools.append(name)
        return self.model_copy()

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        self.seen_messages.append(list(messages))
        if self.responder is not None:
            message = self.responder(list(messages))
        elif self._cursor[0] < len(self.responses):
            message = self.responses[self._cursor[0]]
            self._cursor[0] += 1
        else:
            message = AIMessage(content="[剧本已用完]")
        return ChatResult(generations=[ChatGeneration(message=message)])

    def _stream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        """默认实现是一条整消息；这里切成小块，方便练习流式输出。"""
        result = self._generate(messages, stop, run_manager, **kwargs)
        message = result.generations[0].message
        text = message.content if isinstance(message.content, str) else str(message.content)
        step = max(1, len(text) // 4 or 1)
        pieces = [text[i : i + step] for i in range(0, len(text), step)] or [""]
        for index, piece in enumerate(pieces):
            chunk = ChatGenerationChunk(
                message=AIMessageChunk(
                    content=piece,
                    id=message.id,
                    chunk_position="last" if index == len(pieces) - 1 else None,
                )
            )
            if run_manager is not None:
                run_manager.on_llm_new_token(piece, chunk=chunk)
            yield chunk


def echo_model(*answers: str) -> FakeListChatModel:
    """最省事的假模型：第 n 次调用返回第 n 句。只能用于纯对话、不涉及工具。"""
    return FakeListChatModel(responses=list(answers))


def tool_call(name: str, args: dict[str, Any], call_id: str = "call_1") -> AIMessage:
    """构造一条“我要调用工具”的 AI 消息，等价于真实模型的 function calling 输出。"""
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": call_id}])


def last_human_text(messages: Sequence[BaseMessage]) -> str:
    """取最后一条 HumanMessage 的文本，写 responder 时常用。"""
    for message in reversed(messages):
        if message.type == "human":
            content = message.content
            return content if isinstance(content, str) else str(content)
    return ""
