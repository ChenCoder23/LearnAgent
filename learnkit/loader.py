"""按“练习 / 参考实现”两种模式加载章节代码。

设计意图：每章的题面（``lab.py``）和参考答案（``solutions.py``）是两份**同名函数**的实现。
测试只通过 ``load()`` 取模块，于是同一套测试可以：

- 默认（LEARN_TARGET=lab）跑你写的代码；
- 设置 LEARN_TARGET=solutions 时跑参考答案，用来证明题目和测试本身没问题。
"""

from __future__ import annotations

import importlib
import os
from types import ModuleType

ENV_VAR = "LEARN_TARGET"
VALID_MODES = ("lab", "solutions")


def current_mode() -> str:
    """返回当前模式，非法值直接报错，避免“以为在跑 lab 其实在跑答案”。"""
    mode = os.environ.get(ENV_VAR, "lab").strip().lower() or "lab"
    if mode not in VALID_MODES:
        raise ValueError(f"{ENV_VAR} 只能是 {VALID_MODES}，当前是 {mode!r}")
    return mode


def load(lab: str, mode: str | None = None) -> ModuleType:
    """加载某章的实现模块。

    参数
    ----
    lab:
        章节目录名，例如 ``"01_python_core"``。
    mode:
        ``"lab"``（默认，读你写的代码）或 ``"solutions"``（参考答案）。
    """
    chosen = (mode or current_mode()).lower()
    if chosen not in VALID_MODES:
        raise ValueError(f"mode 只能是 {VALID_MODES}，当前是 {chosen!r}")
    return importlib.import_module(f"labs.{lab}.{chosen}")


def load_source(lab: str, mode: str | None = None) -> str:
    """读取某章源码文本，用于“源码对照”类练习。"""
    module = load(lab, mode)
    with open(module.__file__, encoding="utf-8") as fh:  # type: ignore[arg-type]
        return fh.read()
