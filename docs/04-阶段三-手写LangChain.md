# 阶段三讲义：手写 LangChain（第 14–17 章）

## 为什么要手写一遍

框架的复杂度大部分来自边界情况，但**核心思想往往只有几十行**。
手写一遍的价值是：以后遇到任何新框架，你都能先问「它的执行单元是什么、状态存在哪、错误怎么处理」。

## 14 Runnable：一切可组合

```python
class Runnable(ABC):
    @abstractmethod
    def invoke(self, value, config=None): ...

    def __or__(self, other):
        return RunnableSequence([self, coerce_runnable(other)])
```

关键设计取舍（对照真实 LangChain 想一想）：

| 设计选择 | 收益 | 代价 |
| --- | --- | --- |
| 只要求实现 `invoke` | 新组件极容易接入 | 批处理/流式只能靠默认实现，可能很慢 |
| `__or__` 返回组合对象 | 不用为每对组件写类 | 调试时要在嵌套结构里定位 |
| 函数自动升级为 Runnable | `prompt \| my_func` 直接可用 | 隐式转换可能掩盖错误 |

## 15 检索：向量就是「方向的相似」

余弦相似度只关心方向、不关心长度，所以文本长短不同也能比较。
哈希向量（bigram + md5 → 固定维度）虽然粗糙，但足以让你看清整条链路，而且它**确定**——
这正是能被自动化测试的前提。

工程结论：embedding 质量决定检索上限，切分策略决定下限。

## 16 Agent：循环 + 错误边界

```python
for step in range(max_iterations):
    reply = model.complete(messages, tools)
    if not reply.tool_calls:
        return reply.content
    for call in reply.tool_calls:
        messages.append(Message("tool", execute_tool(tools, call)))   # 永不抛异常
raise MaxIterationsExceeded
```

两个保命机制：**轮数上限**（防止无限循环烧钱）和**工具错误兜底**（防止一个异常毁掉整轮对话）。

## 17 状态图：把 Agent 变成数据流

`StateGraph` 把「控制流」显式化：节点是纯函数、边表达数据依赖、状态可持久化。
有了检查点，你就能实现多轮对话、断点续跑、人工审核——这些在真实业务里是刚需。

```python
merged["messages"] = [*old, *update["messages"]]   # 这就是 reducer（对应 add_messages）
```

reducer 存在的理由：多个节点可能同时写同一个 key，必须有人定义「合并规则」。

## 源码对照任务（阶段三的收尾动作）

打开 `.venv/Lib/site-packages/langchain_core/runnables/base.py`，找这几样并做笔记：

1. `Runnable.__or__` 与 `RunnableSequence`；
2. `batch/stream/astream` 在基类里是怎么被组合出来的；
3. `RunnableRetry`、`RunnableWithFallbacks` 的位置；
4. `BaseChatModel.bind_tools` 到底做了什么（把工具转成 JSON Schema 发给服务端）。

再打开 `langchain/agents/factory.py`，找到 `model_to_tools` 这个路由函数——
那就是你第 17 章 `next_node` 的真实版本（多了并行 `Send`、结构化输出等细节）。

写一份 1 页对照报告，阶段三才算真正收尾。
