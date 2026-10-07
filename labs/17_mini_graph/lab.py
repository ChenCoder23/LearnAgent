"""第 17 章：手写 mini LangGraph —— 状态图、条件边、循环、检查点

依赖：第 14 章。

Agent 循环（第 16 章）其实就是一个“带条件的循环图”。LangGraph 把它抽象成三样东西：

    State    一份共享状态（这里是 dict），节点只返回“要改哪几个字段”
    Node     一个函数：state -> 局部更新
    Edge     下一步去哪：固定边，或者由函数决定的**条件边**

再加一个 Checkpointer：把状态按 thread_id 存起来，就能实现多轮对话、断点续跑、人工审核。

这一章写到 `invoke` 能跑完一张图为止；写完它，LangGraph 的官方概念图你能自己画出来。
"""

from __future__ import annotations

import copy
from collections.abc import Callable
from typing import Any

START = "__start__"
END = "__end__"


class GraphRecursionError(RuntimeError):
    """图跑飞了（比如条件边永远回到自己）。"""


class MemoryCheckpointer:
    """内存版检查点：``put/get`` 都要深拷贝，否则外部改 state 会污染存档。"""

    def __init__(self) -> None:
        raise NotImplementedError("TODO")

    def put(self, thread_id: str, state: dict[str, Any]) -> None:
        raise NotImplementedError("TODO")

    def get(self, thread_id: str) -> dict[str, Any] | None:
        raise NotImplementedError("TODO")


def merge_state(state: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    """合并节点返回的局部更新：

    - 普通 key：覆盖
    - key == ``"messages"`` 且两边都是 list：**追加**（对应 LangGraph 的 add_messages）
    """
    raise NotImplementedError("TODO")


class StateGraph:
    """图定义：节点 + 边。所有 add_* 方法都返回 self，方便链式书写。"""

    def __init__(self) -> None:
        raise NotImplementedError("TODO")

    def add_node(self, name: str, func: Callable[[dict[str, Any]], dict[str, Any] | None]) -> StateGraph:
        raise NotImplementedError("TODO")

    def add_edge(self, source: str, target: str) -> StateGraph:
        """固定边：``add_edge(START, "first")`` 也能用来指定入口。"""
        raise NotImplementedError("TODO")

    def add_conditional_edges(
        self,
        source: str,
        router: Callable[[dict[str, Any]], str],
        mapping: dict[str, str] | None = None,
    ) -> StateGraph:
        """条件边：``router`` 返回一个字符串，先经 ``mapping`` 翻译，再当作目标节点名。"""
        raise NotImplementedError("TODO")

    def set_entry_point(self, name: str) -> StateGraph:
        raise NotImplementedError("TODO")

    def compile(
        self, checkpointer: MemoryCheckpointer | None = None, recursion_limit: int = 25
    ) -> CompiledGraph:
        raise NotImplementedError("TODO")


class CompiledGraph:
    """可执行图：从入口节点开始，按边一步步走，直到 END。"""

    def __init__(
        self,
        nodes: dict[str, Callable[[dict[str, Any]], dict[str, Any] | None]],
        edges: dict[str, str],
        conditional: dict[str, tuple[Callable[[dict[str, Any]], str], dict[str, str] | None]],
        entry: str,
        checkpointer: MemoryCheckpointer | None = None,
        recursion_limit: int = 25,
    ) -> None:
        raise NotImplementedError("TODO")

    def next_node(self, current: str, state: dict[str, Any]) -> str:
        """有固定边先走固定边，否则查条件边；都没有就结束。"""
        raise NotImplementedError("TODO")

    def invoke(self, input_state: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
        """执行整张图。

        - ``config={"configurable": {"thread_id": "t1"}}`` 时，先读检查点、结束后写回；
        - 每走一步都计数，超过 ``recursion_limit`` 抛 ``GraphRecursionError``；
        - 把走过的节点名记在 ``self.history`` 里，方便断言与排查。
        """
        raise NotImplementedError("TODO")
