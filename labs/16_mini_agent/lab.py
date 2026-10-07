"""第 16 章：手写 mini Agent —— 工具定义 + Agent 循环 + ReAct 文本协议

依赖：第 14 章（本章复用它的 Message / BaseChatModel / 假模型）。

Agent 的骨架只有 30 行，真正的难点在工程细节：

1. 怎么把 Python 函数变成模型能理解的“工具描述”（名字、说明、参数）；
2. 工具报错怎么不让整个循环崩掉；
3. 怎么防止模型无限循环（轮数上限 + 明确退出条件）；
4. 怎么把每一步都记录下来，出问题能复盘（可观测性）。

本章做两套：**结构化 tool_calls 协议**（现代做法）和 **ReAct 文本协议**（原始做法）。
看懂两者，LangGraph 那些概念就不再神秘。
"""

from __future__ import annotations

import inspect
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any

from learnkit import load

core = load("14_mini_core")


class MaxIterationsExceeded(RuntimeError):
    """达到最大轮数还没得出结论。"""


@dataclass
class Tool:
    name: str
    description: str
    func: Callable[..., Any]
    parameters: list[str] = field(default_factory=list)


def tool_from_function(func: Callable[..., Any]) -> Tool:
    """把普通函数变成工具：

    - ``name`` 取函数名
    - ``description`` 取 docstring 第一行（所以工具函数必须写 docstring）
    - ``parameters`` 取所有**必填**参数名（用 ``inspect.signature``，跳过 *args/**kwargs 和带默认值的）
    """
    raise NotImplementedError("TODO")


@dataclass
class ToolCall:
    name: str
    args: dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelReply:
    """模型的一轮输出：要么给最终回答，要么要求调用工具。"""

    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)


class ScriptedToolModel:
    """离线假模型：按剧本返回 ``ModelReply``，并记录它看到的消息与工具列表。"""

    def __init__(self, replies: Sequence[ModelReply]) -> None:
        raise NotImplementedError("TODO")

    def complete(self, messages: list[Any], tools: list[Tool]) -> ModelReply:
        raise NotImplementedError("TODO: 剧本用完后返回一条提示性回答")


def execute_tool(tools: list[Tool], call: ToolCall) -> str:
    """执行工具，**永不抛异常**，失败也返回可读文本：

    - 工具不存在 -> ``"错误: 未知工具 xxx"``
    - 缺少参数 -> ``"错误: 工具 xxx 缺少参数 a, b"``
    - 工具内部异常 -> ``"错误: {异常信息}"``

    进阶（测试要求）：模型给过来的参数往往是字符串（"4"），
    如果函数注解是 ``int``/``float``，应该先转换再调用，否则 ``"4" + "5"`` 会变成字符串拼接。
    """
    raise NotImplementedError("TODO")


class AgentExecutor:
    """最小的工具调用 Agent 循环。

    流程::

        messages = [system?, human(question)]
        for step in range(max_iterations):
            reply = model.complete(messages, tools)
            if reply.tool_calls 为空: return reply.content
            执行每个工具，把结果作为 role="tool" 的消息追加进去
        raise MaxIterationsExceeded

    另外要把每一步记录到 ``self.steps``（形如 ``{"step": 1, "tool": "calc", "args": {...},
    "observation": "4"}``），这是排查 Agent 问题唯一可靠的手段。
    """

    def __init__(
        self,
        model: Any,
        tools: Sequence[Tool],
        max_iterations: int = 5,
        system_prompt: str = "需要计算或查数据时必须调用工具，不要臆造。",
    ) -> None:
        raise NotImplementedError("TODO")

    def run(self, question: str) -> str:
        raise NotImplementedError("TODO")


def parse_react(text: str) -> dict[str, Any]:
    """解析 ReAct 文本（不看第 13 章，凭记忆重写一遍）：

    返回 ``{"thought", "action", "action_input", "final_answer"}``，缺失字段为 None。
    前缀大小写不敏感。
    """
    raise NotImplementedError("TODO")


class ReActAgent:
    """文本协议版 Agent：每一步都重新把整个 scratchpad 拼进提示词。

    ``model_fn(prompt: str) -> str`` 是任意“文本进、文本出”的函数（真实项目里就是 LLM 调用）。
    """

    def __init__(
        self, model_fn: Callable[[str], str], tools: Sequence[Tool], max_iterations: int = 5
    ) -> None:
        raise NotImplementedError("TODO")

    def build_prompt(self, question: str) -> str:
        """把工具说明 + scratchpad + 问题拼成 ReAct 提示词。"""
        raise NotImplementedError("TODO")

    def run(self, question: str) -> str:
        """循环：模型输出 -> 解析 -> 若有 Action 就执行并追加 Observation -> 直到 Final Answer。"""
        raise NotImplementedError("TODO")
