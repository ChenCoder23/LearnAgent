"""阶段零 · 第 B 章：判断与循环

先读 `docs/00a-零基础起步.md` 的后半部分，再回来做题。

------------------------------ 本章语法小抄 ------------------------------

1) 缩进就是语法。Python 用**四个空格**的缩进表示「这几行属于上面的 if / for」：

    if age >= 18:
        print("成年")          # 这行有缩进 -> 属于 if
    print("结束")              # 这行没缩进 -> 不管条件如何都会执行

2) 判断：

    if score >= 90:
        grade = "A"
    elif score >= 80:          # elif = else if，可以写很多个
        grade = "B"
    else:
        grade = "C"

   比较运算符：==  !=  >  <  >=  <=        逻辑运算符：and  or  not

3) for 循环：把一串东西**逐个**拿出来用。range(1, 5) 会给出 1,2,3,4（不含 5）。

    total = 0
    for number in range(1, 5):
        total = total + number     # 也可以写成 total += number

4) while 循环：条件为真就一直转，**记得让条件最终会变假**，否则死循环：

    n = 3
    while n > 0:
        print(n)
        n = n - 1

5) break 立刻跳出循环；continue 跳过本次剩下的语句、进入下一轮。

6) 想知道「第几轮」，用 enumerate：

    for index, value in enumerate(["a", "b"]):
        print(index, value)      # 0 a   /   1 b

------------------------------------------------------------------------
"""

from __future__ import annotations


def max_of_three(a: float, b: float, c: float) -> float:
    """返回三个数里最大的那个（不许用内置 max）。"""
    larger = a
    if b > larger:
        larger = b
    if c > larger:
        larger = c
    return larger






def grade(score: int) -> str:
    """百分制转等级：
    - 90 及以上 -> ``"A"``
    - 80 及以上 -> ``"B"``
    - 70 及以上 -> ``"C"``
    - 60 及以上 -> ``"D"``
    - 其他 -> ``"E"``
    - 小于 0 或大于 100 抛 ``ValueError``
    """
    if score < 0 or score > 100:
        raise ValueError("分数必须在 0-100 之间")
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "E"

def sum_to(n: int) -> int:
    """用 for + range 计算 1 + 2 + ... + n；n 小于 1 时返回 0。

    注意 range 的结尾是**开区间**：``range(1, n + 1)`` 才会包含 n。
    """
    total = 0
    for number in  range(1,n):
        total = total + number
    return total



def count_vowels(text: str) -> int:
    """统计字符串里元音字母（a e i o u，忽略大小写）的个数。"""
    count = 0
    for char in text.lower():
        if char in "aeiou":
            count+=1
    return count


def fizzbuzz(n: int) -> list[str]:
    """返回 1..n 的 FizzBuzz 结果列表（含 n）：

    - 3 的倍数 -> ``"Fizz"``
    - 5 的倍数 -> ``"Buzz"``
    - 同时是 3 和 5 的倍数 -> ``"FizzBuzz"``
    - 其他 -> 数字转成的字符串

    判断顺序很重要：先判 15 的倍数，再判 3 和 5。
    """
    raise NotImplementedError("TODO")


def find_first_even(numbers: list[int]) -> int:
    """返回第一个偶数的**下标**；没有偶数返回 -1。用到 break。"""
    raise NotImplementedError("TODO")


def multiplication_row(n: int) -> list[str]:
    """返回 n 的乘法口诀列表，格式 ``"1x3=3"``；n 小于 1 时返回空列表。"""
    raise NotImplementedError("TODO")


def is_prime(n: int) -> bool:
    """判断质数：小于 2 不是质数；只要找到一个能整除它的数就不是质数。

    提示：试到 ``n ** 0.5`` 就够（想一想为什么），找到就 break/return。
    """
    raise NotImplementedError("TODO")


def countdown_while(n: int) -> list[int]:
    """用 while 循环返回 ``[n, n-1, ..., 1]``；n 小于 1 时返回空列表。"""
    raise NotImplementedError("TODO")


def sum_until_over(limit: int) -> tuple[int, int]:
    """用 while 从 1 开始累加，直到和**超过** limit，返回 ``(和, 最后一个加数)``。

    sum_until_over(10) -> (15, 5)   因为 1+2+3+4=10 没超过，加 5 得 15 才超过
    """
    raise NotImplementedError("TODO")


def main() -> None:
    try:
        print(grade(88), sum_to(100), fizzbuzz(15))
        print(countdown_while(3), sum_until_over(10), is_prime(97))
    except NotImplementedError:
        print("还有函数没实现（lab.py 里写着 TODO）。先把它们写完，再运行这个演示。")
        print("也可以先用测试看进度：uv run pytest tests/test_00b_control_flow.py -v")


if __name__ == "__main__":
    main()
