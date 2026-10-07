"""第 13 章测试：工具定义、Agent 循环、工具报错、ReAct 文本协议。"""

from __future__ import annotations

import pytest

pytest.importorskip("langchain")
pytest.importorskip("langgraph")

from langchain_core.messages import AIMessage, ToolMessage  # noqa: E402

from learnkit import load  # noqa: E402
from learnkit.lc_fakes import ScriptedChatModel, tool_call  # noqa: E402

m = load("13_agent_tools")


def test_safe_eval_allows_only_whitelist():
    assert m.safe_eval("2+3*4") == 14
    assert m.safe_eval("(1+2)*3") == 9
    assert m.safe_eval("10/4") == 2.5
    assert m.safe_eval("-3+1") == -2
    for bad in ("2 ** 10", "__import__('os')", "abs(-1)", "1 if True else 2"):
        with pytest.raises(ValueError):
            m.safe_eval(bad)
    with pytest.raises(ValueError):
        m.safe_eval("1/0")


def test_tools_metadata_and_direct_invoke():
    assert m.tool_names([m.calculator, m.get_weather]) == ["calculator", "get_weather"]
    assert m.tool_arguments([m.calculator]) == {"calculator": ["expression"]}
    assert m.calculator.invoke({"expression": "2+3"}) == "5"
    assert m.get_weather.invoke({"city": "郑州"}) == "郑州: 晴 25C"
    with pytest.raises(Exception):
        m.get_weather.invoke({"city": "火星"})
    assert "计算" in (m.calculator.description or "")


def test_agent_calls_tool_then_answers():
    model = ScriptedChatModel(
        responses=[
            tool_call("calculator", {"expression": "12*12"}),
            AIMessage(content="12 乘 12 等于 144。"),
        ]
    )
    agent = m.build_agent(model, [m.calculator, m.get_weather])
    answer = m.ask_agent(agent, "12*12 是多少？")
    assert answer == "12 乘 12 等于 144。"
    assert "calculator" in model.bound_tools, "工具必须被绑定给模型"
    assert len(model.seen_messages) == 2, "模型应该被调用两轮：先出工具调用，再出最终答案"
    observation = [msg for msg in model.seen_messages[1] if isinstance(msg, ToolMessage)]
    assert observation and observation[0].content == "144"


def test_agent_state_exposes_tool_calls():
    model = ScriptedChatModel(
        responses=[
            tool_call("get_weather", {"city": "开封"}),
            AIMessage(content="开封今天小雨。"),
        ]
    )
    agent = m.build_agent(model, [m.get_weather])
    result = agent.invoke({"messages": [{"role": "user", "content": "开封天气"}]})
    assert m.tool_calls_seen(result) == ["get_weather"]
    messages = m.tool_messages(result)
    assert len(messages) == 1
    assert "小雨" in str(messages[0].content)


def test_agent_survives_tool_error():
    safe_weather = m.tolerant_tool(m.get_weather)
    assert safe_weather.name == "get_weather"
    assert list(safe_weather.args) == ["city"]

    model = ScriptedChatModel(
        responses=[
            tool_call("get_weather", {"city": "火星"}),
            AIMessage(content="抱歉，我查不到火星的天气数据。"),
        ]
    )
    agent = m.build_agent(model, [safe_weather])
    result = agent.invoke({"messages": [{"role": "user", "content": "火星天气如何"}]})
    assert result["messages"][-1].content == "抱歉，我查不到火星的天气数据。"
    observations = m.tool_messages(result)
    assert observations and "错误" in str(observations[0].content), "错误会被当作观察结果喂回模型"
    assert observations[0].status != "error", "工具自己处理了错误，循环不该中断"


def test_react_prompt_and_parser_roundtrip():
    prompt = m.build_react_prompt("- calculator: 计算表达式", "3*3 是多少", scratchpad="")
    assert "Action Input:" in prompt and "Final Answer:" in prompt
    assert prompt.rstrip().endswith("开始。") and "Question: 3*3 是多少" in prompt

    raw = """
    Thought: 我需要用计算器
    Action: calculator
    ACTION INPUT: 3*3
    """
    parsed = m.parse_react_output(raw)
    assert parsed["thought"] == "我需要用计算器"
    assert parsed["action"] == "calculator"
    assert parsed["action_input"] == "3*3"
    assert parsed["final_answer"] is None

    final = m.parse_react_output("Thought: 好了\nFinal Answer: 结果是 9")
    assert final["final_answer"] == "结果是 9"
    assert final["action"] is None
    assert m.parse_react_output("啥也没有")["action"] is None
