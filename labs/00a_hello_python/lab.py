"""阶段零 · 第 A 章：变量、类型、运算、输入输出

这一章假设你**完全没写过 Python**。先读 `docs/00a-零基础起步.md` 的前半部分，再回来做题。

怎么运行自己写的代码？在仓库根目录：

    uv run python labs/00a_hello_python/lab.py     # 直接跑这个文件
    uv run pytest tests/test_00a_hello_python.py   # 用测试检查你做得对不对

------------------------------ 本章语法小抄 ------------------------------

1) 变量就是「给值起个名字」，不需要声明类型：

    age = 18            # 整数 int
    price = 9.9         # 小数 float
    name = "小明"        # 字符串 str
    ok = True           # 布尔 bool（只有 True / False 两个值）
    nothing = None      # 空值 None（表示「什么都没有」）

2) 四则运算：+  -  *  /  ；整除 // ；取余 % ；幂 **
   注意：两个整数用 / 相除，结果一定是小数：7 / 2 -> 3.5

3) 字符串拼接与 f-string（推荐）：

    "你好，" + name                       # 老的拼法
    f"你好，{name}！"                     # 推荐：{} 里可以放变量甚至表达式
    f"{price:.2f}"                        # 保留两位小数 -> "9.90"

4) 看一个值是什么类型：type(值).__name__  ->  "int" / "str" / "float" ...

5) 类型转换：int("12") -> 12 ；float("1.5") -> 1.5 ；str(12) -> "12"
   转不动的时候会抛异常（报错）：int("abc") 会抛 ValueError

6) 函数用 def 定义，return 把结果交出去：

    def add(a, b):
        return a + b

------------------------------------------------------------------------

做题方法：每个函数下面写着要求，把 `raise NotImplementedError(...)` 换成你的实现，
然后跑测试。测试失败时先读 `assert` 那一行，它写的就是期望结果。
"""

from __future__ import annotations

import math


def greet(name: str) -> str:
    """返回 ``"你好，<name>！"``。
    greet("小明") -> "你好，小明！"
    """
    raise NotImplementedError("TODO: 用 f-string 拼字符串")


def add(a: float, b: float) -> float:
    """返回 a + b。注意：整数相加结果还是整数，小数的结果类型不用你操心。"""
    raise NotImplementedError("TODO")


def circle_area(radius: float) -> float:
    """返回圆的面积，公式是 π * 半径²。

    提示：π 用 ``math.pi``，平方写成 ``radius ** 2``。
    """
    raise NotImplementedError("TODO")


def celsius_to_fahrenheit(celsius: float) -> float:
    """摄氏温度转华氏温度，公式：摄氏度 × 9 / 5 + 32。"""
    raise NotImplementedError("TODO")


def describe(value: object) -> str:
    """返回这个值的类型名，例如 ``describe(1) -> "int"``、``describe(None) -> "NoneType"``。

    提示：``type(value).__name__``。
    """
    raise NotImplementedError("TODO")


def total_price(price: float, count: int, discount: float = 0.0) -> float:
    """算总价：``price * count * (1 - discount)``。

    ``discount`` 用小数表示折扣：0.1 表示打九折（减价 10%），0 表示不打折。
    这是**默认参数**的第一次见面：调用时不写就用 0。
    """
    raise NotImplementedError("TODO")


def format_receipt(name: str, price: float, count: int) -> str:
    """生成一行小票文本，格式固定为 ``<名字> x<数量> = <总价> 元``，总价保留两位小数。

    format_receipt("苹果", 3.5, 2) -> "苹果 x2 = 7.00 元"
    """
    raise NotImplementedError("TODO: f\"{...} x{...} = {price * count:.2f} 元\"")


def to_int(text: str) -> int:
    """把字符串转成整数；转不了就让它自然抛 ``ValueError``（不要 try/except 吞掉）。

    to_int("12") -> 12
    to_int("abc") -> 抛 ValueError
    """
    raise NotImplementedError("TODO")


def is_adult(age: int) -> bool:
    """满 18 岁返回 True，否则 False。"""
    raise NotImplementedError("TODO")


def swap(a: object, b: object) -> tuple[object, object]:
    """交换两个值并返回 ``(b, a)``。

    提示：Python 里可以直接写 ``b, a``（元组解包），不需要中间变量。
    """
    raise NotImplementedError("TODO")


def average(numbers: list[float]) -> float:
    """求平均值；列表为空时抛 ``ValueError("列表不能为空")``。

    提示：``len(numbers)`` 是元素个数。
    """
    raise NotImplementedError("TODO")


def main() -> None:
    """手动运行时的演示，实现完上面的函数后可以 `uv run python labs/00a_hello_python/lab.py`。"""
    try:
        print(greet("小明"))
        print(add(1, 2), describe(1), describe("a"), describe(None))
        print(format_receipt("苹果", 3.5, 2), total_price(3.5, 2, 0.1))
    except NotImplementedError:
        print("还有函数没实现（lab.py 里写着 TODO）。先把它们写完，再运行这个演示。")
        print("也可以先用测试看进度：uv run pytest tests/test_00a_hello_python.py -v")


if __name__ == "__main__":
    main()
