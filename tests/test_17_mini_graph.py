"""第 17 章测试：状态合并、固定边、条件边、循环、检查点、递归上限。"""

from __future__ import annotations

import pytest

from learnkit import load

m = load("17_mini_graph")
core = load("14_mini_core")


def test_merge_state_overwrites_but_appends_messages():
    state = {"count": 1, "messages": ["a"]}
    merged = m.merge_state(state, {"count": 2, "messages": ["b"]})
    assert merged == {"count": 2, "messages": ["a", "b"]}
    assert state["messages"] == ["a"], "不能修改原 state"


def test_linear_graph_runs_in_order():
    graph = m.StateGraph()
    graph.add_node("first", lambda state: {"count": state["count"] + 1})
    graph.add_node("second", lambda state: {"count": state["count"] * 10})
    graph.add_edge(m.START, "first").add_edge("first", "second").add_edge("second", m.END)
    compiled = graph.compile()
    result = compiled.invoke({"count": 0})
    assert result == {"count": 10}
    assert compiled.history == ["first", "second"]


def test_conditional_edges_with_mapping():
    def router(state):
        return "long" if len(state["text"]) > 3 else "short"

    graph = m.StateGraph()
    graph.add_node("check", lambda state: None)
    graph.add_node("long_node", lambda state: {"result": "LONG"})
    graph.add_node("short_node", lambda state: {"result": "SHORT"})
    graph.set_entry_point("check")
    graph.add_conditional_edges("check", router, {"long": "long_node", "short": "short_node"})
    graph.add_edge("long_node", m.END).add_edge("short_node", m.END)
    compiled = graph.compile()
    assert compiled.invoke({"text": "长长长长"})["result"] == "LONG"
    assert compiled.invoke({"text": "短"})["result"] == "SHORT"


def test_cycle_until_condition_and_recursion_limit():
    graph = m.StateGraph()
    graph.add_node("step", lambda state: {"count": state["count"] + 1})
    graph.set_entry_point("step")
    graph.add_conditional_edges(
        "step", lambda state: "again" if state["count"] < 3 else "done", {"again": "step", "done": m.END}
    )
    compiled = graph.compile()
    assert compiled.invoke({"count": 0})["count"] == 3
    assert compiled.history == ["step", "step", "step"]

    infinite = m.StateGraph()
    infinite.add_node("loop", lambda state: {"count": state["count"] + 1})
    infinite.set_entry_point("loop")
    infinite.add_conditional_edges("loop", lambda state: "loop", {"loop": "loop"})
    with pytest.raises(m.GraphRecursionError):
        infinite.compile(recursion_limit=5).invoke({"count": 0})


def test_checkpointer_keeps_thread_state():
    checkpointer = m.MemoryCheckpointer()
    graph = m.StateGraph()
    graph.add_node("reply", lambda state: {"messages": [core.ai("收到")]})
    graph.set_entry_point("reply").add_edge("reply", m.END)
    compiled = graph.compile(checkpointer=checkpointer)

    first = compiled.invoke(
        {"messages": [core.human("你好")]}, {"configurable": {"thread_id": "t1"}}
    )
    second = compiled.invoke(
        {"messages": [core.human("在吗")]}, {"configurable": {"thread_id": "t1"}}
    )
    assert len(first["messages"]) == 2
    assert len(second["messages"]) == 4, "同一个 thread_id 的历史消息应该累积"
    assert checkpointer.get("t1")["messages"][-1].content == "收到"

    other = compiled.invoke(
        {"messages": [core.human("换个人")]}, {"configurable": {"thread_id": "t2"}}
    )
    assert len(other["messages"]) == 2, "不同 thread 互不影响"
    assert checkpointer.get("t1") is not checkpointer.get("t1"), "取出来的必须是副本"


def test_missing_entry_point_raises():
    with pytest.raises(ValueError):
        m.StateGraph().add_node("a", lambda state: None).compile()
