"""第 16 章测试：工具生成、Agent 循环、错误处理、轮数上限、ReAct 文本协议。"""

from __future__ import annotations

import pytest

from learnkit import load

m = load("16_mini_agent")
core = load("14_mini_core")


def add(a: int, b: int) -> int:
    """把两个整数相加。"""
    return a + b


def boom(reason: str) -> str:
    """永远抛错的工具。"""
    raise ValueError(f"内部错误: {reason}")


def test_tool_from_function_reads_docstring_and_params():
    tool = m.tool_from_function(add)
    assert tool.name == "add"
    assert tool.description == "把两个整数相加。"
    assert tool.parameters == ["a", "b"]

    def with_default(value: int, scale: int = 1) -> int:
        """带默认值的工具。"""
        return value * scale

    assert m.tool_from_function(with_default).parameters == ["value"]


def test_execute_tool_never_raises():
    tools = [m.tool_from_function(add), m.tool_from_function(boom)]
    assert m.execute_tool(tools, m.ToolCall("add", {"a": 1, "b": 2})) == "3"
    assert "未知工具" in m.execute_tool(tools, m.ToolCall("nope", {}))
    assert "缺少参数" in m.execute_tool(tools, m.ToolCall("add", {"a": 1}))
    assert "内部错误" in m.execute_tool(tools, m.ToolCall("boom", {"reason": "x"}))


def test_agent_loop_calls_tool_then_answers():
    model = m.ScriptedToolModel(
        [
            m.ModelReply(tool_calls=[m.ToolCall("add", {"a": 2, "b": 3})]),
            m.ModelReply(content="2 加 3 等于 5。"),
        ]
    )
    agent = m.AgentExecutor(model, [m.tool_from_function(add)])
    assert agent.run("2+3 等于多少") == "2 加 3 等于 5。"
    assert agent.steps == [{"step": 1, "tool": "add", "args": {"a": 2, "b": 3}, "observation": "5"}]
    assert [tool_name for tool_name in model.seen_tools[0]] == ["add"]
    observation = model.seen[1][-1]
    assert observation.role == "tool" and observation.content == "5"


def test_agent_handles_tool_error_and_multiple_calls():
    model = m.ScriptedToolModel(
        [
            m.ModelReply(
                tool_calls=[
                    m.ToolCall("add", {"a": 1, "b": 1}),
                    m.ToolCall("boom", {"reason": "演示"}),
                ]
            ),
            m.ModelReply(content="第一个成功，第二个失败了。"),
        ]
    )
    agent = m.AgentExecutor(model, [m.tool_from_function(add), m.tool_from_function(boom)])
    assert agent.run("同时试两个工具") == "第一个成功，第二个失败了。"
    assert agent.steps[0]["observation"] == "2"
    assert "内部错误" in agent.steps[1]["observation"]


def test_agent_raises_when_iterations_exhausted():
    reply = m.ModelReply(tool_calls=[m.ToolCall("add", {"a": 1, "b": 1})])
    agent = m.AgentExecutor(m.ScriptedToolModel([reply, reply]), [m.tool_from_function(add)], max_iterations=2)
    with pytest.raises(m.MaxIterationsExceeded):
        agent.run("一直循环")


def test_parse_react_and_react_agent():
    parsed = m.parse_react("Thought: 要算一下\nAction: add\nAction Input: 2,3")
    assert parsed["action"] == "add" and parsed["action_input"] == "2,3"
    assert m.parse_react("Final Answer: 结束了")["final_answer"] == "结束了"

    scripted = iter(
        [
            "Thought: 我需要计算\nAction: add\nAction Input: 4,5",
            "Thought: 算出来了\nFinal Answer: 4 加 5 等于 9",
        ]
    )
    prompts: list[str] = []

    def model_fn(prompt: str) -> str:
        prompts.append(prompt)
        return next(scripted)

    agent = m.ReActAgent(model_fn, [m.tool_from_function(add)])
    assert agent.run("4+5 是多少") == "4 加 5 等于 9"
    assert "add(" in prompts[0] and "Question: 4+5 是多少" in prompts[0]
    assert "Observation: 9" in prompts[1], "上一轮的观察结果必须回填进下一轮提示词"
    assert agent.steps[0]["observation"] == "9"
