# 10 · 消息、提示词、流式与解析：语法与设计思路

这一节，咱们先从“字符串不可变，格式化负责把数据变成展示文字”聊起。先理解 Python 的规则和设计思路，再看它们能怎么用。你可以边读边运行小例子，别急着背结论。

咱们先把语言本身讲明白：语法怎么写、代码为什么这样工作、设计上有什么取舍。后面再把这些原理和本节实验联系起来，不按题目挨个拆答案。

## 先聊 Python 的语法和设计思路

这一部分先不看题。咱们从语言规则讲起，用小例子看看它为什么这样工作，再聊这种设计带来的方便和需要留意的地方。后面回到 lab，你就能把代码和这些原理对上。

### 字符串不可变，格式化负责把数据变成展示文字

字符串是一串 Unicode 文本。你调用 strip、replace、upper，得到的是处理后的字符串，原字符串没有被原地改掉。这样同一份字符串被多处共享时，就不用担心别人突然改了内容。

f-string 是把数据放进展示文字的一种方便写法：花括号里可以写变量或表达式，冒号后面可以写格式规则。`:.2f` 表示显示两位小数，处理的是显示样子，不是给后续计算创造一种更精确的数字。

```python
name, price = "茶", 3.5
line = f"{name}: {price:.2f}"
assert line == "茶: 3.50"
assert "  a  b ".split() == ["a", "b"]
assert " / ".join(["a", "b"]) == "a / b"
```

split 把文字拆成小段，join 把小段连起来。join 写在分隔符上，是因为连接时最明确的规则就是“中间插什么”；待连接的内容可以来自列表，也可以来自其他可迭代对象，但每项都得是字符串。文本长度、字符和模型 token 是不同概念，后面做模型上下文预算时还会遇到这个区别。

### 选容器时，先看你要顺序、查找，还是映射

list 适合按顺序保存一组元素，支持追加和下标；tuple 通常用来表达一组固定结构的数据；dict 保存键到值的映射；set 只关心元素有没有出现。没有一种容器能在所有操作上都最好。

比如列表查“有没有这个元素”，通常要一项项比较。集合和字典靠哈希定位，可哈希元素的平均查找成本通常更低，不过它们需要额外内存，还要求键或元素能提供稳定的哈希。列表和字典是可变的，不能直接做 set 元素；元组能否哈希，还要看里面每一项能否哈希。

```python
records = [("a", 1), ("b", 2)]
mapping = dict(records)
assert mapping.get("missing", 0) == 0
assert list(mapping.items()) == records
assert {1, 2, 1} == {1, 2}
```

dict 会保留插入顺序，set 不承诺按你的输入顺序输出。`data[key]` 表示“我期待这个键存在”，缺了就报 KeyError；`data.get(key, default)` 表示“它可能不存在，缺了给我默认值”。这两种写法传达的设计意图不同。

### 迭代协议把数据来源和处理方式分开

for 不需要知道数据来自列表、文件还是无限数字流，它只需要拿到迭代器，再反复请求下一项。可迭代对象提供 __iter__，迭代器提供 __next__，结束时抛 StopIteration。这套小协议让不同数据源能接上同样的处理代码。

```python
source = iter([10, 20])
assert next(source) == 10
assert list(source) == [20]
assert list(source) == []
```

列表本身可以多次创建新迭代器，具体迭代器通常是一次性的。把“可迭代”和“当前这趟遍历的游标”区分开，你就不会奇怪为什么读完后第二次没东西。

函数里有 yield，Python 会替你管理暂停位置，得到生成器。它让逐项处理不用手写完整的游标状态，但计算也延后了，里面的异常可能到 next 时才出现。send 可以把值送回 yield 表达式，第一步通常要先 next 预热；这和 async/await 协程有联系，但普通生成器并不是 asyncio 任务。

### 把变化隔在边界：序列化、接口与生命周期

程序内部有对象，文件和网络上常常是文字或字节。序列化负责把对象变成可传输表示，反序列化负责读回来，但读回来的数据还得检查是不是应用需要的形状。

```python
import json

payload = {"name": "小林", "tags": []}
raw = json.dumps(payload, ensure_ascii=False)
decoded = json.loads(raw)
assert decoded == payload
```

JSON 能表达列表、字典、字符串等常见值，但不直接保留所有 Python 类型和行为。Decimal、datetime、数据库实体通常需要明确转换。语法能解析和业务数据有效，是两个不同的检查点。

接口设计时把数据库对象、API 数据、缓存内容分开，会多一点转换代码，但各层变化不容易互相牵连。资源的生命周期也要有负责人：谁创建会话，谁提交和关闭；谁创建缓存键，谁在数据变化后让它失效。Python 的 with、函数参数和异常协议，正好能帮助表达这些边界。

## 原理明白了，再看看这章会怎样用到它们

### 消息角色

SystemMessage 描述行为要求，HumanMessage 表示用户输入，AIMessage 表示模型回复；history 是已有消息列表，不能直接变成一个字符串塞进去。

### 模板与渲染

ChatPromptTemplate 保存角色与模板，MessagesPlaceholder 插入消息列表。invoke/format_messages 根据 question、history 等字段填值，模板不是渲染后的消息。

### 输出与流式

StrOutputParser 提取文本；stream 输出增量 chunk，收集后拼接得到完整答案。chunk 边界不是词、句子或完整 JSON 的保证。

### 用量与校验

usage_metadata 可能缺失，此时返回零值字典。JsonOutputParser 可处理代码块形式的 JSON，但 title 非空与 tags 为字符串列表仍要显式校验。

### 上下文裁剪

trim_history 保留全部系统消息，其他消息从新到旧选择，并至少保留最后一条；最后恢复原顺序。字符预算是教学近似，不是真实 token 预算。

## 顺着这章，还能多理解一点什么

模板要求输出 JSON 只是提示，解析器和校验才决定应用是否接受回复。离线假模型用于确定性验证；真实 API 的配置参考本目录 real_api_demo.py，语法以仓库实现为准。

## 先看一小段代码，把语法拆开聊

```python
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

prompt = ChatPromptTemplate.from_messages([
    ("system", "用中文回答"),
    MessagesPlaceholder("history", optional=True),
    ("human", "{question}"),
])
messages = prompt.format_messages(question="什么是闭包？")
```

列表中的二元组保存角色和内容，{question} 是模板占位符。optional=True 允许省略 history；question 仍是必须提供的变量。

顺便认一下题目里常见的注解：`list[str]` 是“里面放字符串的列表”，`str | None` 是“字符串或者空值”，`->` 后面写返回什么类型。它们主要是在说明接口，不会替你检查或转换输入。`from __future__ import annotations` 则让注解暂时不求值，第 16 章会用到这个细节。

## 卡住了，先看看这些地方

- 不要把每个流式 chunk 当成累计完整回复。
- 系统消息与最后一条消息可能使最终字符数超过预算，这是题目约定。
- JSON 解析成功不代表字段类型正确。

报错时，先去看失败测试里的 assert 或 pytest.raises：它到底希望得到什么？再回头检查类型、边界和返回值。NotImplementedError 通常是还有一处没写完，ImportError 则先去查环境和依赖。

想确认是不是自己的实现出了问题，可以暂时跑一下参考答案。下面用 finally 把模式切回 lab，省得下次不小心检查了答案，却以为自己做完了。

```powershell
$env:LEARN_TARGET = "solutions"
try {
    uv run pytest tests/test_10_llm_prompt_parser.py -v
} finally {
    $env:LEARN_TARGET = "lab"
}
```

## 先打开哪些文件，怎么跑起来

- [练习文件](lab.py)：填写实现，保留函数名与签名。
- [参考实现](solutions.py)：卡住后对照，理解后合上重写。
- [验收测试](../../tests/test_10_llm_prompt_parser.py)：核对准确输出、错误路径和边界。

打开仓库根目录下的 PowerShell，跑下面这两行。第一行是提醒程序：这次检查你写的 lab，别误跑参考答案。

```powershell
$env:LEARN_TARGET = "lab"
uv run pytest tests/test_10_llm_prompt_parser.py -v
```

想只看一道题，就在命令后面加 `-k 关键词`，关键词可以从链接里的测试文件名和函数名里挑。要是看到 SKIPPED，那是这项没跑，不是做对了；先看看是不是少装了依赖。

## 做完了，试着给自己讲一遍

1. 先合上答案，说说每个函数或类吃进去什么、交回来什么，遇到什么会报错。
2. 挑一个边界例子，比如空输入或刚好卡在阈值上，自己走一遍每一步。
3. 挑一处语法讲给自己听：为什么这么写？换个写法还能不能做，区别在哪里？
4. 最后跑一下 lab 模式的测试。如果有列表、字典或状态，再看看原数据有没有被你不小心改掉。

## 接着往哪一节走

[项目说明](../../README.md) · [学习路线](../../ROADMAP.md) · [上一节](../09_cache_redis/README.md) · [下一节](../11_lcel_runnable/README.md)
