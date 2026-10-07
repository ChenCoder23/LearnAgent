# 三个综合大作业

章节练习是「分解动作」，大作业是「完整比赛」。每个作业都要求：**能跑起来 + 有测试 + 有设计说明**。

## P1 文章服务（阶段一收尾）

把第 08、09 章的代码扩展成一个可运行的服务：

- `app/main.py` 组装 FastAPI，保留第 8 章的分层结构；
- `docker-compose.yml` 起 PostgreSQL + Redis，配置用 `pydantic-settings` 从环境变量读；
- 接口：文章 CRUD + 分页搜索 + 按作者筛选 + 浏览量计数（Redis `INCR`）；
- 缓存：列表页与详情页都用 Cache-Aside；写操作删缓存；热点 key 加 single-flight；
- 异步任务：发布文章后投一条「生成摘要」任务（先用 `asyncio.Queue` 或线程池，进阶换 Celery/RQ）；
- 日志：JSON 格式 + `request_id`，接口耗时打点；
- 测试：覆盖正常路径与失败路径（404/409/422），缓存失效与幂等各写一个测试。

**验收标准**：`docker compose up` 后能在 `/docs` 完成一次完整 CRUD；`pytest` 全绿；
停掉 Redis 后服务**仍能工作**（降级直连数据库，只记警告）。

## P2 知识库问答 Agent（阶段二收尾）

- 数据：把你自己的笔记或博客 Markdown 放进 `data/raw/`；
- 入库脚本：加载 → 切分（保留来源与标题） → embedding → 向量库落盘；
- 问答：RAG 链 + 工具（计算器、数据库查询、时间查询），用 LangGraph 组织状态机；
- 多轮对话：用 checkpointer 按 `thread_id` 保存历史；
- 评估：准备 20 条「问题 → 期望命中来源」样本，写检索命中率脚本；
- 测试：检索命中率脚本 + 假模型下的链路测试 + 「资料不足要说不知道」的测试。

**验收标准**：`python -m project2.eval` 打印命中率；对 3 个真实问题能给出带来源的回答；
问知识库里没有的问题时回答「不知道」。

## P3 用自己的框架复刻 Agent（阶段三收尾）

- 把第 14–17 章的 mini 框架整理成 `minichain/` 包
  （`runnables.py` / `prompts.py` / `retrievers.py` / `agents.py` / `graph.py`）；
- 用 `minichain` 实现 P2 的核心功能（检索问答 + 工具 Agent + 多轮记忆）；
- 写 `docs/comparison.md`：按 ROADMAP 里的对照表逐项对比你的实现与 LangChain 源码；
- 可观测性练习：给每次 `invoke` 打点（耗时、输入摘要、输出摘要），输出 JSON 日志，
  并用它定位一次人为制造的慢请求。

**验收标准**：`minichain` 有独立测试（可复用第 14–17 章的测试思路）；
P2 的功能能用 `minichain` 跑通；对照报告能让别人看懂「框架为什么这样设计」。
