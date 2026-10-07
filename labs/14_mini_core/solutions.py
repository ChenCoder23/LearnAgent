"""第 14 章参考实现：mini LangChain 的骨架。"""

from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Message:
    role: str
    content: str

    def text(self) -> str:
        return self.content


def system(content: str) -> Message:
    return Message(role="system", content=content)


def human(content: str) -> Message:
    return Message(role="human", content=content)


def ai(content: str) -> Message:
    return Message(role="ai", content=content)


def to_messages(value: Any) -> list[Message]:
    if isinstance(value, Message):
        return [value]
    if isinstance(value, str):
        return [human(value)]
    if isinstance(value, (list, tuple)):
        messages: list[Message] = []
        for item in value:
            messages.extend(to_messages(item))
        return messages
    raise TypeError(f"不支持的输入类型: {type(value).__name__}")


class Runnable(ABC):
    @abstractmethod
    def invoke(self, value: Any, config: dict[str, Any] | None = None) -> Any:
        raise NotImplementedError

    def __or__(self, other: Any) -> Runnable:
        return RunnableSequence([self, coerce_runnable(other)])

    def batch(self, values: Sequence[Any], config: dict[str, Any] | None = None) -> list[Any]:
        return [self.invoke(value, config) for value in values]

    def stream(self, value: Any, config: dict[str, Any] | None = None) -> Iterator[Any]:
        yield self.invoke(value, config)

    def with_retry(
        self, times: int = 3, exceptions: tuple[type[BaseException], ...] = (Exception,)
    ) -> Runnable:
        target = self

        def run(value: Any, config: dict[str, Any] | None = None) -> Any:
            for attempt in range(1, times + 1):
                try:
                    return target.invoke(value, config)
                except exceptions:
                    if attempt == times:
                        raise
            raise AssertionError("不可达")

        return RunnableLambda(run)

    def with_fallbacks(self, fallbacks: Sequence[Runnable]) -> Runnable:
        candidates = [self, *(coerce_runnable(item) for item in fallbacks)]

        def run(value: Any, config: dict[str, Any] | None = None) -> Any:
            last_error: BaseException | None = None
            for runnable in candidates:
                try:
                    return runnable.invoke(value, config)
                except Exception as error:  # noqa: BLE001 - 降级就是要兜住
                    last_error = error
            raise last_error  # type: ignore[misc]

        return RunnableLambda(run)

    def map(self) -> Runnable:
        target = self

        def run(values: Sequence[Any], config: dict[str, Any] | None = None) -> list[Any]:
            return [target.invoke(value, config) for value in values]

        return RunnableLambda(run)


class RunnableLambda(Runnable):
    def __init__(self, func: Callable[..., Any]) -> None:
        self.func = func
        parameters = list(inspect.signature(func).parameters.values())
        self.accepts_config = len(parameters) >= 2 or any(
            param.kind is inspect.Parameter.VAR_POSITIONAL for param in parameters
        )

    def invoke(self, value: Any, config: dict[str, Any] | None = None) -> Any:
        if self.accepts_config:
            return self.func(value, config or {})
        return self.func(value)


class RunnableSequence(Runnable):
    def __init__(self, steps: Sequence[Runnable]) -> None:
        if not steps:
            raise ValueError("RunnableSequence 至少要有一个步骤")
        self.steps = list(steps)

    def invoke(self, value: Any, config: dict[str, Any] | None = None) -> Any:
        current = value
        for step in self.steps:
            current = step.invoke(current, config)
        return current

    def stream(self, value: Any, config: dict[str, Any] | None = None) -> Iterator[Any]:
        *head, last = self.steps
        current = value
        for step in head:
            current = step.invoke(current, config)
        yield from last.stream(current, config)

    def __or__(self, other: Any) -> Runnable:
        return RunnableSequence([*self.steps, coerce_runnable(other)])


class RunnableParallel(Runnable):
    def __init__(self, mapping: dict[str, Runnable]) -> None:
        self.mapping = {key: coerce_runnable(value) for key, value in mapping.items()}

    def invoke(self, value: Any, config: dict[str, Any] | None = None) -> dict[str, Any]:
        return {key: runnable.invoke(value, config) for key, runnable in self.mapping.items()}


def coerce_runnable(value: Any) -> Runnable:
    if isinstance(value, Runnable):
        return value
    if callable(value):
        return RunnableLambda(value)
    return RunnableLambda(lambda _value, _config=None: value)


class ChatPromptTemplate(Runnable):
    def __init__(self, messages: Sequence[tuple[str, str]]) -> None:
        self.messages = list(messages)

    @classmethod
    def from_messages(cls, messages: Sequence[tuple[str, str]]) -> ChatPromptTemplate:
        return cls(messages)

    def format_messages(self, **kwargs: Any) -> list[Message]:
        return [
            Message(role=role, content=template.format(**kwargs))
            for role, template in self.messages
        ]

    def invoke(self, value: Any, config: dict[str, Any] | None = None) -> list[Message]:
        if not isinstance(value, dict):
            raise TypeError("ChatPromptTemplate 需要 dict 输入")
        return self.format_messages(**value)


class StrOutputParser(Runnable):
    def invoke(self, value: Any, config: dict[str, Any] | None = None) -> str:
        if isinstance(value, Message):
            return value.content
        if isinstance(value, str):
            return value
        if isinstance(value, (list, tuple)):
            if not value:
                return ""
            return self.invoke(value[-1])
        return str(value)


class BaseChatModel(Runnable):
    def __init__(self) -> None:
        self.seen: list[list[Message]] = []

    @abstractmethod
    def _generate(self, messages: list[Message]) -> Message:
        raise NotImplementedError

    def invoke(self, value: Any, config: dict[str, Any] | None = None) -> Message:
        messages = to_messages(value)
        self.seen.append(messages)
        return self._generate(messages)


class FakeChatModel(BaseChatModel):
    def __init__(self, responses: Sequence[str]) -> None:
        super().__init__()
        self.responses = list(responses)
        self.calls = 0

    def _generate(self, messages: list[Message]) -> Message:
        if self.calls < len(self.responses):
            content = self.responses[self.calls]
            self.calls += 1
            return ai(content)
        return ai("[剧本已用完]")
