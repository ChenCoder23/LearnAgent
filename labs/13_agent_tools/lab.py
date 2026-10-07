"""第 13 章：工具调用与 Agent 循环

Agent 的本质就一句话：**让模型决定下一步做什么，然后用代码去执行，再把结果喂回模型**。

    while 还有工具调用 and 轮数 < 上限:
        模型输出（可能带 tool_calls）
        -> 执行工具
        -> 把结果作为 ToolMessage 追加到消息列表
    返回最后一条 AI 消息

这一章先用 LangChain 的 ``create_agent`` 把这个循环跑通，同时手写解析 ReAct 文本格式的函数
（第三阶段的第 16 章你会亲手把这个循环实现出来）。

所有测试都用离线假模型，工具是本地函数，不联网、不花钱。
"""

from __future__ import annotations

import ast
import operator
from collections.abc import Sequence
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool, tool

DEFAULT_SYSTEM_PROMPT = "你是严谨的中文助手。需要计算或查数据时必须调用工具，不要臆造答案。"

_BIN_OPS: dict[type, Any] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
}
_UNARY_OPS: dict[type, Any] = {ast.USub: operator.neg, ast.UAdd: operator.pos}


def safe_eval(expression: str) -> float:
    """只允许数字与 ``+ - * / // %`` 和括号的表达式求值（白名单方式，禁止 eval）。

    - 出现其他语法（幂运算、函数调用、名字、属性访问）一律抛 ``ValueError``
    - 除以 0 转成 ``ValueError("除数不能为 0")``

    为什么不用 ``eval``？因为 ``eval("__import__('os').system('rm -rf /')")`` 是会真的执行的。
    """
    raise NotImplementedError("TODO: ast.parse(mode='eval') + 递归求值")


@tool
def calculator(expression: str) -> str:
    """计算数学表达式，例如 "1+2*3"。只支持 + - * / // % 和括号。"""
    raise NotImplementedError("TODO: 调 safe_eval，并把结果格式化成字符串")


_WEATHER: dict[str, str] = {"郑州": "晴 25C", "北京": "多云 18C", "开封": "小雨 20C"}


@tool
def get_weather(city: str) -> str:
    """查询指定城市的当前天气。"""
    raise NotImplementedError("TODO: 城市不在数据里就 raise ValueError（让 Agent 学会处理工具报错）")


def tool_names(tools: Sequence[BaseTool]) -> list[str]:
    """返回工具名列表。"""
    raise NotImplementedError("TODO")


def tool_arguments(tools: Sequence[BaseTool]) -> dict[str, list[str]]:
    """返回 ``{工具名: [参数名, ...]}``，用来检查工具的入参 schema 是否自动生成正确。"""
    raise NotImplementedError("TODO: tool.args 或 tool.tool_call_schema.model_json_schema()")


def tolerant_tool(original: BaseTool) -> BaseTool:
    """把工具包装成“永不抛异常”的版本：出错时返回 ``"错误: ..."`` 文本。

    这是本课程最重要的工程经验之一：

    - **可预期错误**（参数不合法、数据不存在）应该在工具内部消化成结构化结果，
      否则 Agent 循环会被异常打断（你可以先把测试改成直接抛，亲眼看看它怎么崩）；
    - **不可预期错误**（代码 Bug）才应该让它抛出，由日志与告警去接。

    实现提示：``StructuredTool.from_function(func=..., name=original.name,
    description=original.description, args_schema=original.args_schema)``。
    """
    raise NotImplementedError("TODO")


def build_agent(
    model: BaseChatModel,
    tools: Sequence[BaseTool],
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
) -> Any:
    """用 ``langchain.agents.create_agent`` 组装 Agent（底层是 LangGraph 状态机）。"""
    raise NotImplementedError("TODO")


def ask_agent(agent: Any, question: str) -> str:
    """跑一轮问答，返回最后一条 AI 消息的文本。"""
    raise NotImplementedError("TODO: agent.invoke({'messages': [{'role': 'user', 'content': question}]})")


def tool_calls_seen(result: dict[str, Any]) -> list[str]:
    """从 Agent 的返回状态里，按顺序取出所有被调用的工具名。"""
    raise NotImplementedError("TODO: 遍历 result['messages'] 里的 AIMessage.tool_calls")


def tool_messages(result: dict[str, Any]) -> list[Any]:
    """取出所有 ToolMessage（工具执行结果，成功或失败都在里面）。"""
    raise NotImplementedError("TODO")


def build_react_prompt(tools_description: str, question: str, scratchpad: str = "") -> str:
    """手写 ReAct 提示词（这是 Agent 的“原始形态”，先看懂它再去看框架实现）。

    返回的文本必须包含：

    - 可用工具说明（``tools_description``）
    - ``Thought:`` / ``Action:`` / ``Action Input:`` / ``Observation:`` 的格式说明
    - ``Final Answer:`` 的结束格式
    - 中间过程 ``scratchpad``（没有就留空）
    - 最后一行 ``Question: <question>``
    """
    raise NotImplementedError("TODO")


def parse_react_output(text: str) -> dict[str, Any]:
    """解析模型按 ReAct 格式吐出的文本，返回::

        {"thought": str | None, "action": str | None, "action_input": str | None,
         "final_answer": str | None}

    要求：

    - 前缀不区分大小写，允许前后有空白
    - 出现 ``Final Answer:`` 时说明已经可以结束（此时 action 为 None）
    - 没有出现的字段用 None 表示
    """
    raise NotImplementedError("TODO: 逐行匹配前缀，别用复杂的正则")
