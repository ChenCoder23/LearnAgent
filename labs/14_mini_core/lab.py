"""第 14 章：手写 mini LangChain —— 模型抽象 + Runnable + 提示词 + 输出解析

从这一章开始，你不再“用框架”，而是**造框架**。用到的只有标准库。

要实现的四件东西，正好对应 LangChain 的四块地基：

    1. Message            统一的消息表示（system / human / ai / tool）
    2. Runnable           统一的执行接口：invoke / batch / stream / __or__
    3. ChatPromptTemplate 把「模板 + 数据」渲染成消息列表
    4. StrOutputParser    把模型输出变成字符串

为什么 ``|`` 这么重要？它把“组合”变成了语言级操作，任何两个 Runnable 都能拼，
框架就不需要为每种组合写一个新类。
"""

from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Message:
    """一条消息。``role`` 取 ``system`` / ``human`` / ``ai`` / ``tool``。"""

    role: str
    content: str

    def text(self) -> str:
        return self.content


def system(content: str) -> Message:
    raise NotImplementedError("TODO")


def human(content: str) -> Message:
    raise NotImplementedError("TODO")


def ai(content: str) -> Message:
    raise NotImplementedError("TODO")


def to_messages(value: Any) -> list[Message]:
    """把各种输入统一成消息列表：

    - ``str`` -> ``[human(str)]``
    - ``Message`` -> ``[value]``
    - ``list`` / ``tuple`` -> 逐个转换后拼接（元素可以是 str 或 Message）
    - 其他 -> 抛 ``TypeError``
    """
    raise NotImplementedError("TODO")


def coerce_runnable(value: Any) -> Runnable:
    """把普通函数/常量自动升级成 Runnable，这样 ``prompt | fn`` 也能用。"""
    raise NotImplementedError("TODO: Runnable 原样返回；callable 包成 RunnableLambda；其他包成常量")


class Runnable(ABC):
    """一切可执行组件的基类。子类只需要实现 ``invoke``。

    其余能力（``|``、batch、stream、重试、降级）都在基类里用 ``invoke`` 组合出来——
    这就是“接口小、能力靠组合”的设计。
    """

    @abstractmethod
    def invoke(self, value: Any, config: dict[str, Any] | None = None) -> Any:
        raise NotImplementedError

    def __or__(self, other: Any) -> Runnable:
        """``a | b``：先跑 a，再把结果喂给 b。"""
        return RunnableSequence([self, coerce_runnable(other)])

    def batch(self, values: Sequence[Any], config: dict[str, Any] | None = None) -> list[Any]:
        return [self.invoke(value, config) for value in values]

    def stream(self, value: Any, config: dict[str, Any] | None = None) -> Iterator[Any]:
        """默认是一次性产出：真正的流式需要模型层支持。"""
        yield self.invoke(value, config)

    def with_retry(
        self, times: int = 3, exceptions: tuple[type[BaseException], ...] = (Exception,)
    ) -> Runnable:
        """失败重试，最多执行 times 次；最后一次仍失败就把异常抛出去。"""
        raise NotImplementedError("TODO: 返回一个新的 Runnable，内部循环调 self.invoke")

    def with_fallbacks(self, fallbacks: Sequence[Runnable]) -> Runnable:
        """依次尝试：自己失败就试 fallbacks[0]，再失败试 fallbacks[1]……"""
        raise NotImplementedError("TODO")

    def map(self) -> Runnable:
        """变成“元素级”Runnable：输入列表，输出对每个元素调用自身后的列表。"""
        raise NotImplementedError("TODO")


class RunnableLambda(Runnable):
    """包装普通函数。函数可以只收 input，也可以收 (input, config)。"""

    def __init__(self, func: Callable[..., Any]) -> None:
        raise NotImplementedError("TODO: 用 inspect.signature 判断参数个数")

    def invoke(self, value: Any, config: dict[str, Any] | None = None) -> Any:
        raise NotImplementedError("TODO")


class RunnableSequence(Runnable):
    """把多个 Runnable 串起来：前一个的输出是后一个的输入。"""

    def __init__(self, steps: Sequence[Runnable]) -> None:
        raise NotImplementedError("TODO")

    def invoke(self, value: Any, config: dict[str, Any] | None = None) -> Any:
        raise NotImplementedError("TODO")

    def stream(self, value: Any, config: dict[str, Any] | None = None) -> Iterator[Any]:
        """流式语义：只有**最后一步**才逐块产出，前面几步必须先算完。"""
        raise NotImplementedError("TODO")

    def __or__(self, other: Any) -> Runnable:
        return RunnableSequence([*self.steps, coerce_runnable(other)])


class RunnableParallel(Runnable):
    """输入一份数据，并行（这里先顺序实现）喂给多个分支，返回字典。"""

    def __init__(self, mapping: dict[str, Runnable]) -> None:
        raise NotImplementedError("TODO: 用 coerce_runnable 处理每个分支")

    def invoke(self, value: Any, config: dict[str, Any] | None = None) -> dict[str, Any]:
        raise NotImplementedError("TODO")


class ChatPromptTemplate(Runnable):
    """聊天提示词模板：内部是一串 ``(role, 模板字符串)``。

    - ``from_messages`` 接收 ``[("system", "..."), ("human", "{question}")]``
    - ``invoke(payload)`` 返回 ``list[Message]``，用 ``str.format(**payload)`` 填充变量
    """

    def __init__(self, messages: Sequence[tuple[str, str]]) -> None:
        raise NotImplementedError("TODO")

    @classmethod
    def from_messages(cls, messages: Sequence[tuple[str, str]]) -> ChatPromptTemplate:
        raise NotImplementedError("TODO")

    def format_messages(self, **kwargs: Any) -> list[Message]:
        raise NotImplementedError("TODO")

    def invoke(self, value: Any, config: dict[str, Any] | None = None) -> list[Message]:
        if not isinstance(value, dict):
            raise TypeError("ChatPromptTemplate 需要 dict 输入")
        return self.format_messages(**value)


class StrOutputParser(Runnable):
    """把消息或字符串统一成 ``str``。"""

    def invoke(self, value: Any, config: dict[str, Any] | None = None) -> str:
        raise NotImplementedError("TODO: Message -> content；str 原样；list -> 取最后一条")


class BaseChatModel(Runnable):
    """模型基类：子类实现 ``_generate``，输入归一化与调用记录由基类负责。"""

    def __init__(self) -> None:
        self.seen: list[list[Message]] = []

    @abstractmethod
    def _generate(self, messages: list[Message]) -> Message:
        raise NotImplementedError

    def invoke(self, value: Any, config: dict[str, Any] | None = None) -> Message:
        raise NotImplementedError("TODO: to_messages(value) -> 记录到 self.seen -> _generate")


class FakeChatModel(BaseChatModel):
    """按剧本回答的假模型：第 n 次调用返回 ``responses[n]``。

    没有假模型就写不出稳定测试：它让“确定性”和“零成本”同时成立。
    """

    def __init__(self, responses: Sequence[str]) -> None:
        raise NotImplementedError("TODO: 别忘了调 super().__init__()")

    def _generate(self, messages: list[Message]) -> Message:
        raise NotImplementedError("TODO: 剧本用完就返回提示信息")
