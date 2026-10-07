"""让 pytest 无论从哪里启动都能 import learnkit / labs。"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def pytest_report_header(config) -> str:
    from learnkit import current_mode

    mode = current_mode()
    label = "练习模式（跑你自己写的 lab.py）" if mode == "lab" else "参考实现模式（solutions.py）"
    return f"LEARN_TARGET = {mode} -> {label}"
