"""第 17 章参考实现。"""

from __future__ import annotations

import copy
from collections.abc import Callable
from typing import Any

START = "__start__"
END = "__end__"


class GraphRecursionError(RuntimeError):
    pass


class MemoryCheckpointer:
    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    def put(self, thread_id: str, state: dict[str, Any]) -> None:
        self._store[thread_id] = copy.deepcopy(state)

    def get(self, thread_id: str) -> dict[str, Any] | None:
        saved = self._store.get(thread_id)
        return copy.deepcopy(saved) if saved is not None else None


def merge_state(state: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    merged = dict(state)
    for key, value in update.items():
        if key == "messages" and isinstance(value, list) and isinstance(merged.get(key), list):
            merged[key] = [*merged[key], *value]
        else:
            merged[key] = value
    return merged


class StateGraph:
    def __init__(self) -> None:
        self.nodes: dict[str, Callable[[dict[str, Any]], dict[str, Any] | None]] = {}
        self.edges: dict[str, str] = {}
        self.conditional: dict[
            str, tuple[Callable[[dict[str, Any]], str], dict[str, str] | None]
        ] = {}
        self.entry: str | None = None

    def add_node(
        self, name: str, func: Callable[[dict[str, Any]], dict[str, Any] | None]
    ) -> StateGraph:
        if name in (START, END):
            raise ValueError(f"{name} 是保留名")
        self.nodes[name] = func
        return self

    def add_edge(self, source: str, target: str) -> StateGraph:
        if source == START:
            self.entry = target
        else:
            self.edges[source] = target
        return self

    def add_conditional_edges(
        self,
        source: str,
        router: Callable[[dict[str, Any]], str],
        mapping: dict[str, str] | None = None,
    ) -> StateGraph:
        self.conditional[source] = (router, mapping)
        return self

    def set_entry_point(self, name: str) -> StateGraph:
        self.entry = name
        return self

    def compile(
        self, checkpointer: MemoryCheckpointer | None = None, recursion_limit: int = 25
    ) -> CompiledGraph:
        if self.entry is None:
            raise ValueError("没有入口节点，请先 set_entry_point 或 add_edge(START, ...)")
        return CompiledGraph(
            nodes=dict(self.nodes),
            edges=dict(self.edges),
            conditional=dict(self.conditional),
            entry=self.entry,
            checkpointer=checkpointer,
            recursion_limit=recursion_limit,
        )


class CompiledGraph:
    def __init__(
        self,
        nodes: dict[str, Callable[[dict[str, Any]], dict[str, Any] | None]],
        edges: dict[str, str],
        conditional: dict[str, tuple[Callable[[dict[str, Any]], str], dict[str, str] | None]],
        entry: str,
        checkpointer: MemoryCheckpointer | None = None,
        recursion_limit: int = 25,
    ) -> None:
        self.nodes = nodes
        self.edges = edges
        self.conditional = conditional
        self.entry = entry
        self.checkpointer = checkpointer
        self.recursion_limit = recursion_limit
        self.history: list[str] = []

    def next_node(self, current: str, state: dict[str, Any]) -> str:
        if current in self.conditional:
            router, mapping = self.conditional[current]
            result = router(state)
            if mapping is not None:
                if result not in mapping:
                    raise KeyError(f"条件边返回了未映射的值: {result!r}")
                result = mapping[result]
            return result
        return self.edges.get(current, END)

    def invoke(
        self, input_state: dict[str, Any], config: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        thread_id = (config or {}).get("configurable", {}).get("thread_id")
        state = dict(input_state)
        if self.checkpointer is not None and thread_id:
            saved = self.checkpointer.get(thread_id)
            if saved is not None:
                state = merge_state(saved, state)

        self.history = []
        current = self.entry
        steps = 0
        while current != END:
            if current not in self.nodes:
                raise KeyError(f"未知节点: {current}")
            steps += 1
            if steps > self.recursion_limit:
                raise GraphRecursionError(f"超过递归上限 {self.recursion_limit} 步")
            self.history.append(current)
            update = self.nodes[current](state)
            if update:
                state = merge_state(state, update)
            current = self.next_node(current, state)

        if self.checkpointer is not None and thread_id:
            self.checkpointer.put(thread_id, state)
        return state
