# learnAgent —— 从 Python 后端到亲手写一个 LangChain

这是一个**练习驱动**的教学项目。它的目标不是让你「看过」，而是让你在完成 20 章练习后，
具备三项可验证的能力：

1. **能独立写 Python 后端**：分层架构、SQL 数据库、缓存、并发、测试、排错；
2. **能用 LangChain 家族开发 Agent**：提示词、LCEL、RAG、工具调用、LangGraph 状态机；
3. **能手写 LangChain**：自己实现 Runnable、Prompt、Retriever、Agent 循环与状态图。

## 一条命令开始

```powershell
uv sync --extra dev --extra stage1 --extra stage2
uv run python -m learnkit.progress
```

第一条命令装依赖（首次约 1 分钟），第二条命令是你的**打卡器**：它会逐章跑测试，
告诉你哪些章已经完成、下一步该写哪个文件。

## 三阶段地图

| 阶段 | 章节 | 学完你能做到 |
| --- | --- | --- |
| 零：零基础起步 | 00a–00c | 变量/类型/运算/字符串、判断与循环、列表与字典；能看懂报错并自己改 |
| 一：语言 + 后端 | 01–09 | 手写装饰器/生成器/值对象；说清 GIL、引用计数、字节码；用 FastAPI + SQLAlchemy 2.0 分层写出带分页、事务、缓存、分布式锁的接口 |
| 二：LangChain + Agent | 10–13 | 写 LCEL 链、RAG 问答、工具调用 Agent；知道什么时候该用 Agent、什么时候不该 |
| 三：手写框架 | 14–17 | 自己实现 Runnable/Prompt/Parser/Retriever/Agent 循环/状态图，并对照真实 LangChain 源码 |

每章的详细目标、验收标准与参考工时见 [ROADMAP.md](ROADMAP.md)。

**完全没写过 Python？** 先读 [docs/00a-零基础起步.md](docs/00a-零基础起步.md)（手把手讲变量、循环、容器、怎么读报错），
再做 `labs/00a` → `labs/00b` → `labs/00c` 三章练习；报错看不懂时查 [docs/06-初学者常见报错速查.md](docs/06-初学者常见报错速查.md)。

## 目录结构

```
labs/00a_hello_python/lab.py        <- 零基础从这里开始（00a/00b/00c 三章）
labs/01_python_core/lab.py          <- 你要写代码的地方（每章一个这样的目录）
labs/01_python_core/solutions.py    <- 参考实现（卡住 30 分钟再看）
tests/test_01_python_core.py        <- 测试就是验收标准
learnkit/loader.py                  <- 决定测试跑你的代码还是参考答案
learnkit/lc_fakes.py                <- 离线假模型，保证不花钱也能练 Agent
learnkit/progress.py                <- 打卡器
docs/                               <- 讲义（学习方法 + 四个阶段文档 + 环境排错）
projects/README.md                  <- 三个综合大作业
```

## 学习循环（每章都这样过）

1. 读讲义 `docs/01-..`、`docs/02-..` 里对应章节，**先看懂要解决什么问题**；
2. 打开 `labs/xx/lab.py`，按 docstring 实现，**函数名与签名不要改**；
3. 跑 `uv run pytest tests/test_xx.py`，看失败信息——测试就是需求文档；
4. 卡住超过 30 分钟，看 `solutions.py`，然后**合上答案重写一遍**；
5. 用一句话向自己解释「为什么这么写」，再跑 `uv run python -m learnkit.progress` 打卡。

## 三条硬规矩

- **必须手打代码**。复制粘贴会跳过最重要的肌肉记忆；`lab.py` 里所有 `NotImplementedError` 都要亲手消灭。
- **不许跳过测试**。每一章的测试都写了边界条件（空输入、越界、并发、失败路径），这些才是真实工程的 80%。
- **不许只看参考答案**。参考答案只有一份；你要能说出「还有哪种写法，各自代价是什么」。

## 常用命令

```powershell
uv run python -m learnkit.progress                  # 打卡：当前进度
uv run python -m learnkit.progress --stage 1        # 只看阶段一
uv run pytest tests/test_02_functions.py -v         # 单章详细测试
$env:LEARN_TARGET="solutions"; uv run pytest        # 用参考实现跑全量测试（验证题目本身）
uv run python labs/06_concurrency_async/demo_gil.py # 手动实验：GIL 对 CPU 密集任务的影响
uv run python labs/07_internals/demo_perf.py        # 手动实验：常见写法的性能差异
uv run ruff check .                                 # 代码风格检查
uv run mypy labs/01_python_core/solutions.py        # 类型检查（先让 solutions 过）
```

## 关于「难度高但通俗」

难度体现在**每一步都要自己动手 + 测试覆盖失败路径**；通俗体现在**每个概念都先用生活化类比讲清，
再给可运行的最小例子**。讲义里所有性能、并发、缓存的结论，你都能用仓库里的脚本亲手复现一遍，
所以不需要背。

## 环境说明

- Python 3.11（由 `.python-version` 固定），用 [uv](https://docs.astral.sh/uv/) 管理依赖；
- 阶段二的测试全部使用离线假模型，**没有 OPENAI_API_KEY 也能做完**；
- 想接真实模型，参考 `labs/10_llm_prompt_parser/real_api_demo.py`；
- `pyproject.toml` 里的 `[tool.uv] cache-dir` 是针对本机 uv 缓存写入报错（os error 17）的临时配置，
  换机器时删掉或改成自己的路径即可。更多排错见 [docs/05-环境搭建与排错.md](docs/05-环境搭建与排错.md)。
