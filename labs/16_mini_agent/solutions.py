"""第 16 章参考实现。"""

from __future__ import annotations

import inspect
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any, get_type_hints

from learnkit import load

core = load("14_mini_core")


class MaxIterationsExceeded(RuntimeError):
    pass


@dataclass
class Tool:
    name: str
    description: str
    func: Callable[..., Any]
    parameters: list[str] = field(default_factory=list)


def tool_from_function(func: Callable[..., Any]) -> Tool:
    doc = inspect.getdoc(func) or ""
    description = doc.splitlines()[0].strip() if doc else f"调用 {func.__name__}"
    parameters: list[str] = []
    for name, parameter in inspect.signature(func).parameters.items():
        if parameter.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            continue
        if parameter.default is inspect.Parameter.empty:
            parameters.append(name)
    return Tool(name=func.__name__, description=description, func=func, parameters=parameters)


@dataclass
class ToolCall:
    name: str
    args: dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelReply:
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)


class ScriptedToolModel:
    def __init__(self, replies: Sequence[ModelReply]) -> None:
        self.replies = list(replies)
        self.calls = 0
        self.seen: list[list[Any]] = []
        self.seen_tools: list[list[str]] = []

    def complete(self, messages: list[Any], tools: list[Tool]) -> ModelReply:
        self.seen.append(list(messages))
        self.seen_tools.append([tool.name for tool in tools])
        if self.calls < len(self.replies):
            reply = self.replies[self.calls]
            self.calls += 1
            return reply
        return ModelReply(content="[剧本已用完]")


def execute_tool(tools: list[Tool], call: ToolCall) -> str:
    table = {tool.name: tool for tool in tools}
    tool = table.get(call.name)
    if tool is None:
        return f"错误: 未知工具 {call.name}"
    missing = [name for name in tool.parameters if name not in call.args]
    if missing:
        return f"错误: 工具 {tool.name} 缺少参数 {', '.join(missing)}"
    try:
        return str(tool.func(**_coerce_args(tool, call.args)))
    except Exception as error:  # noqa: BLE001 - Agent 必须能把工具错误变成观察结果
        return f"错误: {error}"


def _coerce_args(tool: Tool, args: dict[str, Any]) -> dict[str, Any]:
    """模型给的多半是字符串，这里按函数注解把 int/float 转回去。

    坑：一旦文件里写了 ``from __future__ import annotations``，
    ``signature().parameters[...].annotation`` 拿到的是**字符串** ``"int"`` 而不是 ``int``，
    所以要用 ``get_type_hints`` 解析。
    """
    hints = get_type_hints(tool.func)
    coerced: dict[str, Any] = {}
    for name, value in args.items():
        target = hints.get(name)
        if isinstance(value, str) and target in (int, float):
            try:
                coerced[name] = target(value)
                continue
            except ValueError:
                coerced[name] = value
                continue
        coerced[name] = value
    return coerced


class AgentExecutor:
    def __init__(
        self,
        model: Any,
        tools: Sequence[Tool],
        max_iterations: int = 5,
        system_prompt: str = "需要计算或查数据时必须调用工具，不要臆造。",
    ) -> None:
        self.model = model
        self.tools = list(tools)
        self.max_iterations = max_iterations
        self.system_prompt = system_prompt
        self.steps: list[dict[str, Any]] = []

    def run(self, question: str) -> str:
        messages: list[Any] = [core.system(self.system_prompt), core.human(question)]
        for step in range(1, self.max_iterations + 1):
            reply = self.model.complete(messages, self.tools)
            if not reply.tool_calls:
                return reply.content
            messages.append(core.ai(reply.content))
            for call in reply.tool_calls:
                observation = execute_tool(self.tools, call)
                self.steps.append(
                    {
                        "step": step,
                        "tool": call.name,
                        "args": dict(call.args),
                        "observation": observation,
                    }
                )
                messages.append(core.Message(role="tool", content=observation))
        raise MaxIterationsExceeded(f"{self.max_iterations} 轮内没有得出结论")


def parse_react(text: str) -> dict[str, Any]:
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
                if result[key] is None:
                    result[key] = line[len(prefix) :].strip()
                break
    if result["final_answer"] is not None:
        result["action"] = None
        result["action_input"] = None
    return result


class ReActAgent:
    def __init__(
        self, model_fn: Callable[[str], str], tools: Sequence[Tool], max_iterations: int = 5
    ) -> None:
        self.model_fn = model_fn
        self.tools = list(tools)
        self.max_iterations = max_iterations
        self.scratchpad = ""
        self.steps: list[dict[str, Any]] = []

    def build_prompt(self, question: str) -> str:
        lines = ["你可以使用以下工具："]
        for tool in self.tools:
            params = ", ".join(tool.parameters) or "无参数"
            lines.append(f"- {tool.name}({params}): {tool.description}")
        lines.append("")
        lines.append("按下面格式回答（每轮只做一个动作）：")
        lines.append("Thought: 你的思考")
        lines.append("Action: 工具名")
        lines.append("Action Input: 工具入参")
        lines.append("Observation: 系统填写的工具结果")
        lines.append("... 完成后用：")
        lines.append("Thought: 我知道答案了")
        lines.append("Final Answer: 中文最终回答")
        lines.append("")
        if self.scratchpad:
            lines.append(self.scratchpad.strip())
        lines.append(f"Question: {question}")
        lines.append("开始。")
        return "\n".join(lines)

    def run(self, question: str) -> str:
        self.scratchpad = ""
        for step in range(1, self.max_iterations + 1):
            output = self.model_fn(self.build_prompt(question))
            parsed = parse_react(output)
            if parsed["final_answer"]:
                return parsed["final_answer"]
            if not parsed["action"]:
                return output.strip()
            tool = next((item for item in self.tools if item.name == parsed["action"]), None)
            if tool is None or not tool.parameters:
                args: dict[str, Any] = {}
            elif len(tool.parameters) == 1:
                args = {tool.parameters[0]: parsed["action_input"] or ""}
            else:
                raw = parsed["action_input"] or ""
                parts = [piece.strip() for piece in raw.split(",")]
                args = (
                    dict(zip(tool.parameters, parts, strict=True))
                    if len(parts) == len(tool.parameters)
                    else {"input": raw}
                )
            call = ToolCall(name=parsed["action"], args=args)
            observation = execute_tool(self.tools, call)
            self.steps.append(
                {"step": step, "action": parsed["action"], "observation": observation}
            )
            self.scratchpad += (
                f"Thought: {parsed['thought'] or ''}\n"
                f"Action: {parsed['action']}\n"
                f"Action Input: {parsed['action_input'] or ''}\n"
                f"Observation: {observation}\n"
            )
        raise MaxIterationsExceeded(f"{self.max_iterations} 轮内没有得出结论")
