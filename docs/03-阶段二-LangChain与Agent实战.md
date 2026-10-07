# 阶段二讲义：LangChain 与 Agent 实战（第 10–13 章）

## 先建立正确的世界观

LLM 应用只有三种形态，先判断你属于哪一种，再选工具：

| 形态 | 特征 | 用什么 |
| --- | --- | --- |
| 单轮生成 | 输入→输出，无状态 | 直接调用模型 |
| 固定流程 | 步骤确定，只是某几步用模型 | LCEL 链（**优先选它**） |
| 自主决策 | 下一步做什么取决于上一步结果 | Agent / LangGraph |

能用固定流程解决的，不要上 Agent：Agent 更贵、更慢、更难测、更容易跑飞。

## 消息与提示词

四种角色：`system`（规则与边界）、`human`（用户输入）、`ai`（模型输出）、`tool`（工具结果）。
多轮对话就是把历史消息一起发过去——所以**上下文管理**（裁剪、摘要）迟早要面对。

```python
prompt = ChatPromptTemplate.from_messages([
    ("system", "只依据资料回答，资料不足就说不知道"),
    MessagesPlaceholder("history", optional=True),
    ("human", "资料：\n{context}\n\n问题：{question}"),
])
```

实用经验：**把约束写成可检验的句子**（「必须输出 JSON，字段为 a/b」），比写「请你专业一点」有效得多。

## LCEL：一个符号统一所有组合

```python
chain = prompt | model | StrOutputParser()
chain.invoke({"question": "..."})
chain.batch([...])            # 批量
chain.stream({...})           # 流式
await chain.ainvoke({...})    # 异步
```

每个 Runnable 都自带 `with_retry` / `with_fallbacks`，所以「换模型、加重试、加降级」不改业务代码。
这就是接口设计的胜利，第 14 章你要自己实现一遍。

## RAG：效果不好时按顺序排查

```
1. 切分：chunk 是否把答案切散了？overlap 够不够？metadata 是否保留？
2. 检索：top-k 里到底有没有正确片段？（先把检索结果打出来看，不要猜）
3. 提示词：资料塞进去了吗？是否要求「只依据资料」？
4. 模型：换更强模型是否能解决？代价可接受吗？
```

经验值：RAG 的问题里大多数出在切分与检索，不在模型。

## Agent：循环 + 工具

```python
agent = create_agent(model=model, tools=[calculator, get_weather])
result = agent.invoke({"messages": [{"role": "user", "content": "..."}]})
```

工具设计的四条纪律：

1. **docstring 就是给模型看的说明书**，必须写清「什么时候用」；
2. 参数尽量少、类型明确，能用枚举就别放自由字符串；
3. **可预期错误在工具内消化**并返回「错误: ...」文本，否则 Agent 循环会直接崩；
4. 工具有副作用（发邮件、下单）时，要么加人工确认，要么做成幂等。

## 可观测性与成本

- 记录每一步：模型输入输出、工具名与参数、耗时、token 用量（`usage_metadata`）；
- 用 `config={"tags": [...]}` 给链路打标，方便接追踪平台；
- 控制成本：`max_iterations` 上限、检索 top-k 别开太大、长历史做摘要压缩。

## 离线测试策略（本项目的做法）

真实 LLM 是不确定的，把测试写成「问一句、比对答案」必然失败。正确做法是分层测试：

| 层 | 怎么测 |
| --- | --- |
| 提示词渲染 | 断言渲染出的消息内容（确定性） |
| 输出解析 | 喂固定文本，断言解析结果（确定性） |
| 链路接线 | 用假模型断言「检索结果确实进了提示词」 |
| Agent 循环 | 用剧本式假模型断言「工具被调用、观察结果被回填」 |
| 真实模型 | 只做少量人工冒烟测试 + 人工评估集 |

本项目 `learnkit/lc_fakes.py` 里的 `ScriptedChatModel` 就是干这个用的。
