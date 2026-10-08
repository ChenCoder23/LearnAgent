# 16 · 手写工具、Agent 循环与 ReAct：语法与设计思路

这一节，咱们先从“反射读到的是声明，不能代替所有验证”聊起。先理解 Python 的规则和设计思路，再看它们能怎么用。你可以边读边运行小例子，别急着背结论。

咱们先把语言本身讲明白：语法怎么写、代码为什么这样工作、设计上有什么取舍。后面再把这些原理和本节实验联系起来，不按题目挨个拆答案。

## 先聊 Python 的语法和设计思路

这一部分先不看题。咱们从语言规则讲起，用小例子看看它为什么这样工作，再聊这种设计带来的方便和需要留意的地方。后面回到 lab，你就能把代码和这些原理对上。

### 反射读到的是声明，不能代替所有验证

Python 对象能告诉你自己的名字、类型、文档和函数签名。inspect.signature 让你在运行时看参数，get_type_hints 让你解析注解，所以插件、依赖注入和工具描述都可以从普通函数出发。

```python
import inspect

def greet(name: str, prefix="Hi"):
    return f"{prefix}, {name}"

sig = inspect.signature(greet)
assert sig.parameters["name"].default is inspect.Parameter.empty
assert sig.parameters["prefix"].default == "Hi"
```

Parameter.empty 表示没写默认值，和默认值是 None 不同。参数还分位置专用、位置或关键字、关键字专用以及 *args/**kwargs，不能只看名字就假定都能用 **kwargs 调用。

反射降低重复写元信息的成本，但也增加了隐式行为。函数注解写 int，不代表字符串一定能安全转换，bool、联合类型、嵌套对象更不是简单调用一次类型就完事。适配器最好说清支持范围，复杂需求交给更完整的绑定和校验逻辑。

### 类型注解是在沟通接口，运行时校验是另一件事

`name: str`、`list[int]`、`-> bool` 都是在说明这段代码希望怎样被使用。普通 Python 函数不会因为写了注解就自动挡住错误类型，类型检查器能提前找一部分问题，运行时约束还要靠显式检查或校验库。

```python
def echo(value: int) -> int:
    return value

assert echo("text") == "text"  # 运行时不会因为注解自动拒绝
```

泛型描述的是类型之间的关系：Page[T] 里 items 是 T，映射到 U 后变成 Page[U]，而不是把分页信息全丢掉。Protocol 写出组件需要具备的方法，让接口和具体存储实现分开。

本仓库用 future annotations 延迟求值注解，因此反射时可能看到字符串形式的注解。需要拿到 int、float 等实际类型对象时，用 get_type_hints 解析。类型注解不是完整输入 schema：范围、必填、长度、字段间关系还需要另外描述和验证。

### 异常让正常结果和失败原因走不同通道

函数如果拿不到结果，返回 0 或空字符串有时会把“失败”混成“合法结果”。异常提供另一条通道：正常情况 return，做不了时 raise，外层决定在哪一层恢复或报告。

```python
def lookup(data, key):
    try:
        return data[key]
    except KeyError as error:
        raise ValueError(f"找不到 {key}") from error
```

except 只接住你能处理的错误，没必要到处 catch Exception。except 内裸 raise 会保留当前异常继续传播；raise ... from error 则把业务层错误和底层根因连起来。try 的 else 只在正常完成时走，finally 用于无论成败都要做的收尾。

该不该把异常转成普通数据，要看接口。批量任务可能希望收集每项失败，工具执行器可能希望模型看见错误观察；但转换后也得明确标记失败，别和成功结果混淆。finally 里随意 return 还可能覆盖原结果和异常，通常不要这么做。

### 状态机：把“记什么”和“下一步去哪”分开

有循环的流程容易把判断、数据修改和重试都塞进一大块代码。状态机把它们拆开：状态保存当前信息，节点根据状态做工作，路由决定下一站。用 Python 的字典和函数就能表达这个结构。

```python
def step(state):
    return {"count": state["count"] + 1}

state = {"count": 0, "messages": []}
state = {**state, **step(state)}
destination = "again" if state["count"] < 3 else "done"
assert destination == "again"
```

节点返回局部更新，合并器决定怎么处理：普通字段可能覆盖，消息可能追加。这样“更新怎么算”和“更新怎么并入旧状态”可以分别修改和测试。

浅拷贝字典只隔开外层，里面的列表仍可能共享。要让存档真的像快照，保存和读取时都要考虑拷贝策略。循环上限按业务步骤数记录，可以挡住路由一直回自己的情况；它不是 Python 函数递归深度。图结构让流程更可见，也会增加抽象层，简单的一次调用不用急着上图。

## 原理明白了，再看看这章会怎样用到它们

### 工具元信息

inspect.signature 提取必填参数，inspect.getdoc 取得描述。Tool.parameters 只是必填参数名列表，不是完整 JSON Schema；带默认值与可变参数会跳过。

### 参数转换

模型可能给 "4" 而不是 4。get_type_hints 解析延迟注解，再对 int/float 做转换；不能只使用 signature.annotation，因为 future annotations 可使它成为字符串。

### 执行与观察

execute_tool 先查工具、查必填参数，再调用并把结果转文本；未知工具、缺参、执行失败都返回“错误:”观察。Agent 可以根据错误再尝试。

### 循环与记录

AgentExecutor 每轮调用 complete；无 tool_calls 就返回内容，否则执行所有调用并追加 tool 消息，steps 保存轮次、参数和观察。达到最大模型调用轮数抛专用异常。

### 文本 Agent

ReActAgent 重建提示词和 scratchpad，解析 Action Input 并调用同样的执行器；多参数用逗号拆分，是教学协议，不能处理所有复杂 JSON 或含逗号的字符串。

## 顺着这章，还能多理解一点什么

ScriptedToolModel 让测试能验证模型实际收到的消息和工具列表。工具调用 Agent 与 ReAct 只是动作协议不同，执行器、停止上限与观察结果的职责相同。

## 先看一小段代码，把语法拆开聊

```python
import inspect
from typing import get_type_hints

def add(a: int, b: int = 1) -> int:
    """两个数相加。"""
    return a + b

signature = inspect.signature(add)
required = [name for name, param in signature.parameters.items()
            if param.default is inspect.Parameter.empty]
assert required == ["a"]
assert get_type_hints(add)["a"] is int
```

inspect.Parameter.empty 是“没有默认值”的哨兵，不是 None。get_type_hints 返回实际类型对象，后续可以用 int("4") 做转换。

顺便认一下题目里常见的注解：`list[str]` 是“里面放字符串的列表”，`str | None` 是“字符串或者空值”，`->` 后面写返回什么类型。它们主要是在说明接口，不会替你检查或转换输入。`from __future__ import annotations` 则让注解暂时不求值，第 16 章会用到这个细节。

## 卡住了，先看看这些地方

- 工具调用后至少还需一次模型回复才可能得出最终答案。
- default_factory 防止多个 ToolCall 或 ModelReply 共享列表字典。
- 参考 steps 会累积，多次 run 的追踪隔离是可选改进点。

报错时，先去看失败测试里的 assert 或 pytest.raises：它到底希望得到什么？再回头检查类型、边界和返回值。NotImplementedError 通常是还有一处没写完，ImportError 则先去查环境和依赖。

想确认是不是自己的实现出了问题，可以暂时跑一下参考答案。下面用 finally 把模式切回 lab，省得下次不小心检查了答案，却以为自己做完了。

```powershell
$env:LEARN_TARGET = "solutions"
try {
    uv run pytest tests/test_16_mini_agent.py -v
} finally {
    $env:LEARN_TARGET = "lab"
}
```

## 先打开哪些文件，怎么跑起来

- [练习文件](lab.py)：填写实现，保留函数名与签名。
- [参考实现](solutions.py)：卡住后对照，理解后合上重写。
- [验收测试](../../tests/test_16_mini_agent.py)：核对准确输出、错误路径和边界。

打开仓库根目录下的 PowerShell，跑下面这两行。第一行是提醒程序：这次检查你写的 lab，别误跑参考答案。

```powershell
$env:LEARN_TARGET = "lab"
uv run pytest tests/test_16_mini_agent.py -v
```

想只看一道题，就在命令后面加 `-k 关键词`，关键词可以从链接里的测试文件名和函数名里挑。要是看到 SKIPPED，那是这项没跑，不是做对了；先看看是不是少装了依赖。

## 做完了，试着给自己讲一遍

1. 先合上答案，说说每个函数或类吃进去什么、交回来什么，遇到什么会报错。
2. 挑一个边界例子，比如空输入或刚好卡在阈值上，自己走一遍每一步。
3. 挑一处语法讲给自己听：为什么这么写？换个写法还能不能做，区别在哪里？
4. 最后跑一下 lab 模式的测试。如果有列表、字典或状态，再看看原数据有没有被你不小心改掉。

## 接着往哪一节走

[项目说明](../../README.md) · [学习路线](../../ROADMAP.md) · [上一节](../15_mini_rag/README.md) · [下一节](../17_mini_graph/README.md)
