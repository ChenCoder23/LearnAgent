"""第 14 章测试：手写框架的组装能力（不依赖任何第三方库）。"""

from __future__ import annotations

import pytest

from learnkit import load

m = load("14_mini_core")


def test_message_helpers_and_to_messages():
    assert m.system("s").role == "system"
    assert m.human("h").role == "human"
    assert m.ai("a").role == "ai"
    assert m.to_messages("你好")[0] == m.human("你好")
    assert m.to_messages(m.ai("嘿")) == [m.ai("嘿")]
    mixed = m.to_messages(["纯文本", m.ai("AI 消息")])
    assert [item.role for item in mixed] == ["human", "ai"]
    with pytest.raises(TypeError):
        m.to_messages(3)


def test_prompt_template_and_output_parser():
    prompt = m.ChatPromptTemplate.from_messages(
        [("system", "你是{role}"), ("human", "{question}")]
    )
    messages = prompt.invoke({"role": "助教", "question": "什么是闭包"})
    assert messages[0].content == "你是助教"
    assert messages[1].role == "human"
    assert m.StrOutputParser().invoke(messages) == "什么是闭包"
    assert m.StrOutputParser().invoke("已是字符串") == "已是字符串"


def test_pipe_operator_builds_a_chain():
    prompt = m.ChatPromptTemplate.from_messages([("human", "{question}")])
    model = m.FakeChatModel(["闭包就是携带了环境的函数"])
    chain = prompt | model | m.StrOutputParser()
    assert chain.invoke({"question": "什么是闭包"}) == "闭包就是携带了环境的函数"
    assert model.seen[0][0].content == "什么是闭包"


def test_sequence_supports_functions_and_batch():
    double = m.RunnableLambda(lambda value: value * 2)
    chain = double | (lambda value: value + 1)
    assert chain.invoke(3) == 7
    assert chain.batch([1, 2, 3]) == [3, 5, 7]
    assert chain.stream(2) is not None
    assert list(chain.stream(2)) == [5], "默认流式就是一次性产出"


def test_parallel_and_map():
    parallel = m.RunnableParallel(
        {"upper": m.RunnableLambda(str.upper), "length": m.RunnableLambda(len)}
    )
    assert parallel.invoke("abc") == {"upper": "ABC", "length": 3}
    assert m.RunnableLambda(str.upper).map().invoke(["a", "b"]) == ["A", "B"]


def test_retry_and_fallback():
    state = {"calls": 0}

    def flaky(value: int) -> int:
        state["calls"] += 1
        if state["calls"] < 3:
            raise ValueError("再试")
        return value

    assert m.RunnableLambda(flaky).with_retry(times=3).invoke(9) == 9
    assert state["calls"] == 3

    def boom(_value):
        raise RuntimeError("主链挂了")

    chain = m.RunnableLambda(boom).with_fallbacks([m.RunnableLambda(lambda value: f"降级:{value}")])
    assert chain.invoke("x") == "降级:x"

    with pytest.raises(RuntimeError):
        m.RunnableLambda(boom).with_retry(times=2).invoke("x")


def test_config_is_forwarded_to_lambda():
    captured: dict[str, object] = {}

    def with_config(value: int, config: dict) -> int:
        captured["config"] = config
        return value + 1

    assert m.RunnableLambda(with_config).invoke(1, {"tags": ["mini"]}) == 2
    assert captured["config"] == {"tags": ["mini"]}


def test_stream_only_streams_last_step():
    def gen(value: int):
        yield from range(value)

    class Streamer(m.Runnable):
        def invoke(self, value, config=None):
            return list(gen(value))

        def stream(self, value, config=None):
            yield from gen(value)

    chain = m.RunnableLambda(lambda value: value * 2) | Streamer()
    assert list(chain.stream(3)) == [0, 1, 2, 3, 4, 5]


def test_fake_model_runs_out_of_script():
    model = m.FakeChatModel(["第一次"])
    assert model.invoke("a").content == "第一次"
    assert model.invoke("b").content == "[剧本已用完]"
    assert model.calls == 1
