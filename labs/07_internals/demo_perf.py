"""手动实践：常见写法的性能对比，跑一遍比背结论有用得多。

跑法：uv run python labs/07_internals/demo_perf.py
"""

from __future__ import annotations

import timeit

N = 100_000


def setup() -> str:
    return "data = list(range(1000)); pairs = list(zip(range(1000), range(1000)))"


CASES = {
    "字符串 += 拼接": "s = ''\nfor i in range(1000): s += str(i)",
    "列表 append + join": "parts = []\nfor i in range(1000): parts.append(str(i))\ns = ''.join(parts)",
    "列表推导式": "[n * 2 for n in data]",
    "for + append": "out = []\nfor n in data: out.append(n * 2)",
    "字典 get": "total = 0\nfor k, v in pairs: total += {}.get(k, 0)",
    "sum 生成器": "sum(n for n in data)",
    "sum 推导式": "sum([n for n in data])",
}


def main() -> None:
    print(f"每个用例执行 {N} 次，单位秒\n")
    results = sorted(
        ((name, timeit.timeit(code, setup=setup(), number=N)) for name, code in CASES.items()),
        key=lambda item: item[1],
    )
    for name, elapsed in results:
        print(f"{name:<22}{elapsed:8.4f}")


if __name__ == "__main__":
    main()
