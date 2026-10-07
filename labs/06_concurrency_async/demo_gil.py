"""手动实践：亲眼看看 GIL 对 CPU 密集任务的影响。

跑法：uv run python labs/06_concurrency_async/demo_gil.py

预期现象（在普通 4 核以上机器上）：

    串行        : ~1.0s
    多线程(4)   : ~1.0s   <- 几乎没变快，因为 GIL 只允许一个线程执行 Python 字节码
    多进程(4)   : ~0.3s   <- 真并行

IO 密集任务则相反：多线程会有明显加速（见 test_06 里的 run_threads 对比）。
"""

from __future__ import annotations

import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

ITERATIONS = 6_000_000


def cpu_task(n: int = ITERATIONS) -> int:
    total = 0
    for i in range(n):
        total += i * i % 7
    return total


def main() -> None:
    jobs = 4

    started = time.perf_counter()
    for _ in range(jobs):
        cpu_task()
    print(f"串行        : {time.perf_counter() - started:.2f}s")

    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=jobs) as executor:
        list(executor.map(cpu_task, [ITERATIONS] * jobs))
    print(f"多线程({jobs})   : {time.perf_counter() - started:.2f}s")

    started = time.perf_counter()
    with ProcessPoolExecutor(max_workers=jobs) as executor:
        list(executor.map(cpu_task, [ITERATIONS] * jobs))
    print(f"多进程({jobs})   : {time.perf_counter() - started:.2f}s")


if __name__ == "__main__":  # Windows 上多进程必须要有这个守卫
    main()
