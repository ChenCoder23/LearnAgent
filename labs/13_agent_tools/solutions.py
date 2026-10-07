"""第 13 章参考实现。"""

from __future__ import annotations

import ast
import operator
from collections.abc import Sequence
from typing import Any

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool, StructuredTool, tool

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


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        if isinstance(node.value, bool):
            raise ValueError("不支持布尔值")
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        operation = _BIN_OPS[type(node.op)]
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        if isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)) and right == 0:
            raise ValueError("除数不能为 0")
        return float(operation(left, right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return float(_UNARY_OPS[type(node.op)](_eval_node(node.operand)))
    raise ValueError(f"不支持的表达式节点: {type(node).__name__}")


def safe_eval(expression: str) -> float:
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as error:
        raise ValueError(f"表达式语法错误: {expression!r}") from error
    return _eval_node(tree.body)


@tool
def calculator(expression: str) -> str:
    """计算数学表达式，例如 "1+2*3"。只支持 + - * / // % 和括号。"""
    return f"{safe_eval(expression):g}"


_WEATHER: dict[str, str] = {"郑州": "晴 25C", "北京": "多云 18C", "开封": "小雨 20C"}


@tool
def get_weather(city: str) -> str:
    """查询指定城市的当前天气。"""
    if city not in _WEATHER:
        raise ValueError(f"没有 {city} 的天气数据")
    return f"{city}: {_WEATHER[city]}"


def tool_names(tools: Sequence[BaseTool]) -> list[str]:
    return [item.name for item in tools]


def tool_arguments(tools: Sequence[BaseTool]) -> dict[str, list[str]]:
    return {item.name: list(item.args) for item in tools}


def tolerant_tool(original: BaseTool) -> BaseTool:
    def run(**kwargs: Any) -> str:
        try:
            return str(original.invoke(kwargs))
        except Exception as error:  # noqa: BLE001 - 这里就是要兜住所有可预期错误
            return f"错误: {error}"

    return StructuredTool.from_function(
        func=run,
        name=original.name,
        description=(original.description or "").strip(),
        args_schema=original.args_schema,
    )


def build_agent(
    model: BaseChatModel,
    tools: Sequence[BaseTool],
    system_prompt: str = DEFAULT_SYSTEM_PROMPT,
) -> Any:
    return create_agent(model=model, tools=list(tools), system_prompt=system_prompt)


def ask_agent(agent: Any, question: str) -> str:
    result = agent.invoke({"messages": [{"role": "user", "content": question}]})
    last = result["messages"][-1]
    content = last.content
    return content if isinstance(content, str) else str(content)


def tool_calls_seen(result: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for message in result.get("messages", []):
        for call in getattr(message, "tool_calls", None) or []:
            name = call.get("name") if isinstance(call, dict) else getattr(call, "name", None)
            if name:
                names.append(name)
    return names


def tool_messages(result: dict[str, Any]) -> list[ToolMessage]:
    return [message for message in result.get("messages", []) if isinstance(message, ToolMessage)]


def build_react_prompt(tools_description: str, question: str, scratchpad: str = "") -> str:
    return (
        "你有以下工具可以使用：\n"
        f"{tools_description}\n\n"
        "按下面的格式一步步推理（每轮只能做一个动作）：\n"
        "Thought: 你的思考\n"
        "Action: 工具名（必须是上面列出的工具之一）\n"
        "Action Input: 工具入参\n"
        "Observation: 工具返回结果（由系统填写，你不要自己编）\n"
        "...（Thought/Action/Action Input/Observation 可以重复多轮）\n"
        "当你已经能回答时，用：\n"
        "Thought: 我已经知道答案了\n"
        "Final Answer: 最终回答（用中文）\n\n"
        f"{scratchpad}"
        f"Question: {question}\n"
        "开始。"
    )


def parse_react_output(text: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "thought": None,
        "action": None,
        "action_input": None,
        "final_answer": None,
    }
    prefixes = {
        "thought:": "thought",
        "action input:": "action_input",
        "action:": "action",
        "final answer:": "final_answer",
    }
    for raw_line in text.splitlines():
        line = raw_line.strip()
        lower = line.lower()
        for prefix, key in prefixes.items():
            if lower.startswith(prefix):
                value = line[len(prefix) :].strip()
                if result[key] is None:
                    result[key] = value
                break
    if result["final_answer"] is not None:
        result["action"] = None
        result["action_input"] = None
    return result
