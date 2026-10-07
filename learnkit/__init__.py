"""learnkit：这个教学项目的练习运行器。

学习者只需要记住三个入口：

1. ``load("01_python_core")``  在测试里拿到当前章节的实现（默认是你写的 lab.py）。
2. ``LEARN_TARGET=solutions``  对照参考实现跑测试，验证题目本身是对的。
3. ``python -m learnkit.progress``  查看全部章节的完成度。
"""

from learnkit.loader import current_mode, load, load_source

__all__ = ["load", "load_source", "current_mode"]
