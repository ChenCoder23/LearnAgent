"""第 1 章：语法核心 —— 数据类型、容器、字符串、可变性

零基础先修：变量 / if / for / 字典还不熟？先做 labs/00a、00b、00c 三章，
讲义是 docs/00a-零基础起步.md，报错看不懂查 docs/06-初学者常见报错速查.md。

目标（做完才算过）：

1. 能用容器 + 推导式表达“分组 / 去重 / 展平 / 切片”这类日常数据整形。
2. 说清楚 **可变对象与不可变对象的区别**，以及为什么默认参数不能写 ``[]``。
3. 知道 ``dict`` / ``list`` / ``set`` / ``tuple`` 各自在什么场景下最快。

练习方式（每一章都一样）：

    ① 读讲义 docs/01-阶段一-语言基础与原理.md 的对应小节
    ② 在这里实现，函数名和签名不要改
    ③ 跑测试：uv run pytest tests/test_01_python_core.py
    ④ 卡住超过 30 分钟，看同目录 solutions.py，然后**合上答案重写一遍**
    ⑤ 用一句话向自己解释：为什么这么写？有没有第二种写法？

提示：本章所有题目都**不允许 import re**（除了第 2 题允许，但你最好先手写一遍）。
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from typing import Any


def dedupe(seq: Iterable[Any]) -> list[Any]:
    """保序去重：保留每个元素**第一次**出现的位置，返回 list。

    要求：元素可哈希，时间复杂度 O(n)。

    >>> dedupe([3, 1, 3, 2, 1])
    [3, 1, 2]
    """
    raise NotImplementedError("TODO: 用 set 记录见过的元素，同时 append 到结果 list")


def parse_version(text: str) -> dict[str, Any]:
    """解析语义化版本号 ``major.minor.patch[-pre][+build]``。

    返回示例::

        parse_version("1.2.3")            -> {"major": 1, "minor": 2, "patch": 3, "pre": None, "build": None}
        parse_version("1.2.3-rc.1+b5")    -> {"major": 1, "minor": 2, "patch": 3, "pre": "rc.1", "build": "b5"}

    规则：

    - 三段数字必须存在，且必须是非负整数，多余的前导零允许（"01" -> 1）。
    - ``-pre`` 与 ``+build`` 都是可选的，顺序固定：先 ``-`` 后 ``+``。
    - 任何不合法输入抛 ``ValueError``，消息里带上原始输入。
    """
    raise NotImplementedError("TODO: 先切 '+'，再切 '-'，然后 split('.') 校验三段")


def group_by(items: Iterable[Any], key: str | Callable[[Any], Any]) -> dict[Any, list[Any]]:
    """按 key 分组。``key`` 既可以是函数，也可以是字典的字段名。

    >>> group_by([{"t": "a", "v": 1}, {"t": "b", "v": 2}, {"t": "a", "v": 3}], "t")
    {'a': [{'t': 'a', 'v': 1}, {'t': 'a', 'v': 3}], 'b': [{'t': 'b', 'v': 2}]}
    """
    raise NotImplementedError("TODO: 用 dict.setdefault 或 defaultdict，注意 key 为 str 时要取字段")


def flatten(nested: Iterable[Any], *, skip_none: bool = True) -> list[Any]:
    """把任意深度的 list/tuple 展平成一维 list。

    - 只把 list/tuple 当作容器，字符串和 dict 属于**叶子节点**，整体保留。
    - ``skip_none=True`` 时丢弃 None。

    >>> flatten([1, [2, (3, None)], "ab"])
    [1, 2, 3, 'ab']
    """
    raise NotImplementedError("TODO: 递归；注意 isinstance(True, int) 这类陷阱与 str 的处理")


def chunk(seq: Sequence[Any], size: int) -> list[list[Any]]:
    """把序列切成固定大小的块，最后一块可以更短。

    ``size <= 0`` 抛 ``ValueError``。空序列返回 ``[]``。

    >>> chunk([1, 2, 3, 4, 5], 2)
    [[1, 2], [3, 4], [5]]
    """
    raise NotImplementedError("TODO: 用 range(0, len(seq), size) + 切片")


def deep_get(data: Any, path: str, default: Any = None) -> Any:
    """按 ``"a.b.0.c"`` 这样的路径取值，取不到返回 default。

    规则：

    - 路径段是纯数字时对 list/tuple 按下标取值，越界返回 default。
    - dict 缺 key 返回 default。
    - 中途遇到 None / 类型不匹配，返回 default（不要抛异常）。

    >>> deep_get({"a": {"b": [{"c": 7}]}}, "a.b.0.c")
    7
    """
    raise NotImplementedError("TODO: 逐段走，任何一步失败就 return default")


def normalize(text: str) -> str:
    """文本归一化：去首尾空白、内部连续空白压成一个半角空格、去掉零宽字符。

    ``\\u3000``（全角空格）、``\\t``、``\\n``、``\\u200b`` 都算空白或需剔除。

    >>> normalize("  hello\\u3000 world\\u200b ")
    'hello world'
    """
    raise NotImplementedError("TODO: str.split() 默认就按任意空白切分，把零宽字符先替换掉")


def summarize(nums: Sequence[float]) -> dict[str, float]:
    """返回 ``{"min", "max", "mean", "median"}``。

    中位数：奇数个取中间值，偶数个取中间两个的平均值。空序列抛 ``ValueError``。
    注意不要因为追求性能把可读性写没了：先排序再取，O(n log n) 足够。

    >>> summarize([1, 3, 2, 4])
    {'min': 1, 'max': 4, 'mean': 2.5, 'median': 2.5}
    """
    raise NotImplementedError("TODO: median 用 sorted；偶数个时 (a+b)/2")


def add_tag(tag: str, tags: list[str] | None = None) -> list[str]:
    """返回**新的** list，内容是把 tag 追加到 tags 之后。

    这是 Python 最经典的坑：``def add_tag(tag, tags=[])`` 会让所有调用共享同一个 list。
    本函数要求：不修改传入的 tags，也不允许把可变对象当默认值。

    >>> add_tag("a")
    ['a']
    >>> add_tag("b", ["a"])
    ['a', 'b']
    """
    raise NotImplementedError("TODO: 想想 tags is None 时该做什么，而不是参数默认写 []")


def merge_config(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """深合并两个配置字典，返回新字典，**不能修改任何入参**。

    规则：两边同一个 key 都是 dict 时递归合并；否则 override 的值整体替换 base 的值。

    >>> merge_config({"db": {"host": "a", "port": 1}}, {"db": {"port": 2}})
    {'db': {'host': 'a', 'port': 2}}
    """
    raise NotImplementedError("TODO: 用 copy.deepcopy 起手，或写纯函数式递归（更推荐）")
