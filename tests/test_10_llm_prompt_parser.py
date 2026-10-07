"""第 10 章测试：消息、模板、解析、裁剪（全离线）。"""

from __future__ import annotations

import pytest

pytest.importorskip("langchain_core")

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage  # noqa: E402

from learnkit import load  # noqa: E402
from learnkit.lc_fakes import ScriptedChatModel  # noqa: E402

m = load("10_llm_prompt_parser")


def test_build_messages_variants():
    messages = m.build_messages("sys", [HumanMessage(content="之前")], "现在呢")
    assert [type(item).__name__ for item in messages] == [
        "SystemMessage",
        "HumanMessage",
        "HumanMessage",
    ]
    assert messages[0].content == "sys"
    assert messages[-1].content == "现在呢"
    assert m.build_messages("", None, "") == []


def test_prompt_template_renders_history_placeholder():
    template = m.build_prompt_template("你是助教")
    messages = m.render_prompt(
        template, "第二问", history=[HumanMessage(content="第一问"), AIMessage(content="第一答")]
    )
    assert [type(item).__name__ for item in messages] == [
        "SystemMessage",
        "HumanMessage",
        "AIMessage",
        "HumanMessage",
    ]
    assert messages[-1].content == "第二问"
    assert len(m.render_prompt(template, "只有一问")) == 2


def test_ask_model_uses_script():
    model = ScriptedChatModel(responses=[AIMessage(content="你好，我是假模型")])
    assert m.ask_model(model, "你好") == "你好，我是假模型"
    assert model.seen_messages[0][0].type == "system"
    assert model.seen_messages[0][-1].content == "你好"


def test_stream_tokens_reassembles_answer():
    model = ScriptedChatModel(responses=[AIMessage(content="流式输出的内容")])
    chunks = m.stream_tokens(model, "讲一下流式")
    assert len(chunks) >= 2
    assert "".join(chunks) == "流式输出的内容"


def test_extract_usage_defaults_and_real_values():
    assert m.extract_usage(AIMessage(content="没有用量信息")) == {
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
    }
    message = AIMessage(
        content="有用量",
        usage_metadata={"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
    )
    assert m.extract_usage(message) == {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15}


def test_parse_article_json_handles_fences_and_errors():
    raw = """```json
    {"title": "  标题  ", "tags": ["a", "b"]}
    ```"""
    assert m.parse_article_json(raw) == {"title": "标题", "tags": ["a", "b"], "content": ""}
    assert m.parse_article_json('{"title": "T"}')["tags"] == []
    with pytest.raises(ValueError):
        m.parse_article_json('{"title": "   "}')
    with pytest.raises(ValueError):
        m.parse_article_json('{"title": "T", "tags": [1, 2]}')


def test_trim_history_keeps_system_and_newest():
    messages = [
        SystemMessage(content="S" * 10),
        HumanMessage(content="A" * 10),
        AIMessage(content="B" * 10),
        HumanMessage(content="C" * 10),
    ]
    trimmed = m.trim_history(messages, max_chars=25)
    assert isinstance(trimmed[0], SystemMessage)
    assert [item.content for item in trimmed[1:]] == ["B" * 10, "C" * 10]
    assert m.trim_history([], 10) == []
    only_system = m.trim_history([SystemMessage(content="S")], 0)
    assert len(only_system) == 1
    huge = m.trim_history([HumanMessage(content="X" * 500)], 10)
    assert len(huge) == 1, "至少保留最后一条"
