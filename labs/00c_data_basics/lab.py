"""阶段零 · 第 C 章：字符串、列表、字典（Python 最常用的三样东西）

做完这一章，你就具备了进入第 01 章的所有前提。

------------------------------ 本章语法小抄 ------------------------------

1) 字符串常用操作：

    s = "Hello World"
    s.lower()            # "hello world"（原本的 s 不会变）
    s.split()            # ["Hello", "World"]（按空白切开，变成列表）
    s.split(",")         # 按逗号切开
    ",".join(["a", "b"]) # "a,b"（把列表粘回字符串）
    s.replace("l", "L")  # 替换
    s.strip()            # 去掉首尾空白
    len(s)               # 长度
    s[0]                 # 第 0 个字符（下标从 0 开始！）
    for ch in s: ...     # 逐个字符

2) 列表：有顺序、可修改的一串东西

    numbers = [3, 1, 2]
    numbers.append(9)    # 末尾追加 -> [3, 1, 2, 9]
    numbers[0]           # 3
    numbers[-1]          # 9（负数表示从后往前数）
    len(numbers)         # 4
    for x in numbers: ...

3) 字典：键 -> 值 的映射，用来「按名字查东西」

    ages = {"小明": 18, "小红": 20}
    ages["小明"]              # 18
    ages.get("小刚", 0)       # 不存在时返回默认值 0（不会报错）
    ages["小刚"] = 21         # 新增/修改
    for name, age in ages.items(): ...     # 同时拿到键和值
    "小明" in ages            # 判断键在不在

4) 遍历时同时要下标用 enumerate；遍历字典用 .items()

------------------------------------------------------------------------
"""

from __future__ import annotations




def count_chars(text: str) -> dict[str, int]:
    """统计每个字符出现的次数。

    count_chars("aba") -> {"a": 2, "b": 1}

    提示：用 ``result[ch] = result.get(ch, 0) + 1``。
    """




def word_count(sentence: str) -> dict[str, int]:
    """统计每个单词出现的次数（按空白切分）。

    word_count("a b a") -> {"a": 2, "b": 1}
    """




def reverse_words(sentence: str) -> str:
    """把单词顺序反过来：``reverse_words("hello world") -> "world hello"``。"""







def capitalize_words(sentence: str) -> str:
    """每个单词首字母大写：``capitalize_words("hello world") -> "Hello World"``。

    提示：字符串有 ``.capitalize()`` 或 ``.title()`` 方法，想想区别。
    """



def filter_even(numbers: list[int]) -> list[int]:
    """返回只包含偶数的**新列表**（用 for + append 写，别用列表推导式，那是第 01 章的内容）。"""




def list_stats(numbers: list[float]) -> dict[str, float]:
    """返回 ``{"min": 最小值, "max": 最大值, "sum": 总和, "count": 个数}``；空列表抛 ValueError。

    提示：内置函数 ``min`` / ``max`` / ``sum`` / ``len`` 可以直接用。
    """




def pairs_to_dict(pairs: list[tuple[str, int]]) -> dict[str, int]:
    """把 ``[("a", 1), ("b", 2)]`` 转成 ``{"a": 1, "b": 2}``。

    提示：``for key, value in pairs:``。
    """




def get_or_default(data: dict[str, int], key: str, default: int) -> int:
    """取字典里的值，键不存在就返回 default（不要用会报错的 ``data[key]`` 写法）。"""



def remove_duplicates(items: list[int]) -> list[int]:
    """去掉重复元素，**保持第一次出现的顺序**：``[1, 2, 1] -> [1, 2]``。

    提示：先建一个空列表，遍历时用 ``if item not in result:`` 判断。
    """



def join_names(names: list[str], sep: str = ", ") -> str:
    """把名字列表拼成一个字符串，默认用逗号加空格分隔。

    join_names(["a", "b"]) -> "a, b"      join_names(["a", "b"], "-") -> "a-b"
    """


def find_max_key(data: dict[str, int]) -> str | None:
    """返回值最大的那个键；空字典返回 None。

    find_max_key({"a": 1, "b": 3}) -> "b"
    """






def main() -> None:
    try:
        print(count_chars("aba"), word_count("a b a"))
        print(reverse_words("hello world"), capitalize_words("hello world"))
        print(list_stats([1, 2, 3]), remove_duplicates([1, 2, 1]), join_names(["a", "b"]))
    except NotImplementedError:
        print("还有函数没实现（lab.py 里写着 TODO）。先把它们写完，再运行这个演示。")
        print("也可以先用测试看进度：uv run pytest tests/test_00c_data_basics.py -v")


if __name__ == "__main__":
    main()
