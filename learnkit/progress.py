"""学习打卡器：``uv run python -m learnkit.progress``

它会逐章跑测试，告诉你哪些章已经「过」了，哪些还没动手，并给出下一步建议。

常用参数：

    --mode lab        跑你自己写的代码（默认）
    --mode solutions  跑参考实现，用来确认题目本身是对的
    --stage 2         只看第二阶段的章节
    --verbose         打印 pytest 的完整输出（调试自己的实现时很有用）
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class Chapter:
    lab: str
    title: str
    stage: int
    hours: float


CHAPTERS: tuple[Chapter, ...] = (
    Chapter("00a_hello_python", "零基础 A：变量、类型、运算、字符串", 0, 4),
    Chapter("00b_control_flow", "零基础 B：判断与循环", 0, 4),
    Chapter("00c_data_basics", "零基础 C：字符串、列表、字典", 0, 4),
    Chapter("01_python_core", "语法核心：类型、容器、可变性", 1, 6),
    Chapter("02_functions", "函数、作用域、闭包、装饰器", 1, 6),
    Chapter("03_oop", "面向对象与魔术方法", 1, 8),
    Chapter("04_iter_gen_exc", "迭代器、生成器、上下文管理器、异常", 1, 8),
    Chapter("05_typing_log", "类型注解、Protocol、Pydantic、结构化日志", 1, 6),
    Chapter("06_concurrency_async", "并发与异步：GIL、线程、进程、asyncio", 1, 8),
    Chapter("07_internals", "Python 原理：对象模型、内存、字节码、拷贝", 1, 6),
    Chapter("08_fastapi_sql", "FastAPI + SQLAlchemy 2.0 分层后端", 1, 12),
    Chapter("09_cache_redis", "缓存与 Redis：三大问题、分布式锁、幂等、限流", 1, 8),
    Chapter("10_llm_prompt_parser", "LangChain 起步：消息、模板、输出解析", 2, 6),
    Chapter("11_lcel_runnable", "Runnable 与 LCEL：组合、并行、重试、降级", 2, 6),
    Chapter("12_rag", "RAG：切分、embedding、向量库、检索、问答", 2, 8),
    Chapter("13_agent_tools", "工具调用与 Agent 循环（LangChain create_agent）", 2, 8),
    Chapter("14_mini_core", "手写 LangChain：Runnable + Prompt + Parser", 3, 8),
    Chapter("15_mini_rag", "手写 RAG：切分、向量、检索、链", 3, 8),
    Chapter("16_mini_agent", "手写 Agent：工具、循环、ReAct 协议", 3, 8),
    Chapter("17_mini_graph", "手写 mini LangGraph：状态图与检查点", 3, 8),
)

STAGE_NAMES = {
    0: "阶段零：Python 零基础起步（完全没写过代码就从这里开始）",
    1: "阶段一：Python 语言 + 后端（数据库/缓存）",
    2: "阶段二：LangChain 与 Agent 实战",
    3: "阶段三：手写 LangChain 家族",
}


@dataclass
class Outcome:
    chapter: Chapter
    passed: int
    failed: int
    returncode: int
    output: str

    @property
    def ok(self) -> bool:
        # 以退出码为唯一判据；统计数字只用于展示（pytest 的安静级别会影响输出格式）
        return self.returncode == 0


COUNT_RE = re.compile(r"(\d+) (passed|failed|error)")


def run_chapter(chapter: Chapter, mode: str) -> Outcome:
    import os

    env = dict(os.environ)
    env["LEARN_TARGET"] = mode
    env.setdefault("PYTHONUTF8", "1")
    completed = subprocess.run(  # noqa: S603
        [sys.executable, "-m", "pytest", f"tests/test_{chapter.lab}.py", "--no-header"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    output = completed.stdout + completed.stderr
    passed = failed = 0
    for count, kind in COUNT_RE.findall(output):
        if kind == "passed":
            passed = int(count)
        elif kind in ("failed", "error"):
            failed += int(count)
    return Outcome(chapter, passed, failed, completed.returncode, output)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="learnAgent 学习进度打卡")
    parser.add_argument("--mode", default="lab", choices=["lab", "solutions"])
    parser.add_argument("--stage", type=int, default=None, choices=[0, 1, 2, 3])
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    selected = [c for c in CHAPTERS if args.stage in (None, c.stage)]
    print(f"模式: {args.mode}   章节数: {len(selected)}\n")

    outcomes: list[Outcome] = []
    current_stage = None
    for chapter in selected:
        if chapter.stage != current_stage:
            current_stage = chapter.stage
            print(f"== {STAGE_NAMES[current_stage]} ==")
        outcome = run_chapter(chapter, args.mode)
        outcomes.append(outcome)
        mark = "✓" if outcome.ok else "✗"
        if outcome.ok and outcome.passed == 0:
            detail = "全部通过"
        else:
            detail = f"{outcome.passed} 过 / {outcome.failed} 未过"
        print(f"  {mark} {chapter.lab:<24} {chapter.title:<40} {detail}")
        if args.verbose and not outcome.ok:
            print(outcome.output)

    done = [o for o in outcomes if o.ok]
    percent = 100 * len(done) / len(outcomes) if outcomes else 0
    hours = sum(o.chapter.hours for o in outcomes if o.ok)
    print(f"\n完成度: {len(done)}/{len(outcomes)} 章（{percent:.0f}%），累计练习时长约 {hours}h")

    todo = next((o for o in outcomes if not o.ok), None)
    if todo is None:
        print("全部完成。恭喜——接下来去做 projects/README.md 里的综合项目。")
    else:
        print(f"下一步: 打开 labs/{todo.chapter.lab}/lab.py，跑 uv run pytest tests/test_{todo.chapter.lab}.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
