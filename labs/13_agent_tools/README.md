# 13 · 工具调用 Agent 与 ReAct：语法与设计思路

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

### 装饰器就是包装，保留什么、改变什么得说清楚

`@decorate` 放在函数上方，基本意思是先创建函数，再把它交给 decorate，最后用返回的对象替换原名字。语言给的是一个简洁入口，具体增加缓存、日志还是权限，都是普通函数在完成。

```python
from functools import wraps

def decorate(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper
```

定义里的 *args 收集位置参数，**kwargs 收集关键字参数；调用里的星号把它们展开回去。wraps 帮你保留名称、文档和 __wrapped__ 等信息，但不会自动验证参数，也不会替包装逻辑保住正确的返回值和异常行为。

带配置的装饰器通常再包一层：外层收配置，返回装饰器，装饰器再收目标函数。这个设计让“配置一次”和“调用很多次”分开。重试、缓存这些包装可能改变副作用发生的次数，所以设计时还要想想目标函数重复执行是否安全。

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

### 安全表达式

safe_eval 用 ast.parse(..., mode="eval") 解析表达式并递归检查白名单节点，只执行允许的数字、二元/一元运算。函数调用、名字、属性、幂等节点都拒绝。

### 工具声明

@tool 根据名称、docstring、类型注解建立工具说明和参数 schema；tool_arguments 检查模型能看到的字段。get_weather 是课程模拟数据，不查询实时天气。

### 工具容错

tolerant_tool 保留原 args_schema，并将函数执行错误转换为错误文本。框架的参数 schema 校验可能发生在函数包装前；转换执行错误不代表所有外部错误都被吞掉。

### 结构化循环

create_agent 组装模型和工具；ask_agent 传 messages 并取最后 AI 文本，tool_calls_seen 从 AI 消息读取调用记录，tool_messages 收集执行结果。

### 文本协议

ReAct 用 Thought、Action、Action Input、Observation、Final Answer 描述循环。parse_react_output 忽略前缀大小写，缺失字段为 None，有最终答案时停止工具动作。

## 顺着这章，还能多理解一点什么

文本协议更易看到过程，但也更容易格式漂移；结构化工具调用用 schema 限定参数形状。参数合法与操作有权限仍是不同层面，实际系统应独立控制可用工具。

## 先看一小段代码，把语法拆开聊

```python
import ast

node = ast.parse("1 + 2 * 3", mode="eval").body
assert isinstance(node, ast.BinOp)
assert isinstance(node.op, ast.Add)
# 这里只检查结构；求值需要逐层验证允许的节点和运算符
```

mode="eval" 解析单个表达式，.body 取得表达式节点。isinstance 检查节点类型，不会运行表达式文本。

顺便认一下题目里常见的注解：`list[str]` 是“里面放字符串的列表”，`str | None` 是“字符串或者空值”，`->` 后面写返回什么类型。它们主要是在说明接口，不会替你检查或转换输入。`from __future__ import annotations` 则让注解暂时不求值，第 16 章会用到这个细节。

## 卡住了，先看看这些地方

- 禁止用 eval 替代 AST 白名单。
- 工具结果需作为 ToolMessage 回到循环，不能只有日志。
- Final Answer 出现后 action 必须清空，避免继续执行旧动作。

报错时，先去看失败测试里的 assert 或 pytest.raises：它到底希望得到什么？再回头检查类型、边界和返回值。NotImplementedError 通常是还有一处没写完，ImportError 则先去查环境和依赖。

想确认是不是自己的实现出了问题，可以暂时跑一下参考答案。下面用 finally 把模式切回 lab，省得下次不小心检查了答案，却以为自己做完了。

```powershell
$env:LEARN_TARGET = "solutions"
try {
    uv run pytest tests/test_13_agent_tools.py -v
} finally {
    $env:LEARN_TARGET = "lab"
}
```

## 先打开哪些文件，怎么跑起来

- [练习文件](lab.py)：填写实现，保留函数名与签名。
- [参考实现](solutions.py)：卡住后对照，理解后合上重写。
- [验收测试](../../tests/test_13_agent_tools.py)：核对准确输出、错误路径和边界。

打开仓库根目录下的 PowerShell，跑下面这两行。第一行是提醒程序：这次检查你写的 lab，别误跑参考答案。

```powershell
$env:LEARN_TARGET = "lab"
uv run pytest tests/test_13_agent_tools.py -v
```

想只看一道题，就在命令后面加 `-k 关键词`，关键词可以从链接里的测试文件名和函数名里挑。要是看到 SKIPPED，那是这项没跑，不是做对了；先看看是不是少装了依赖。

## 做完了，试着给自己讲一遍

1. 先合上答案，说说每个函数或类吃进去什么、交回来什么，遇到什么会报错。
2. 挑一个边界例子，比如空输入或刚好卡在阈值上，自己走一遍每一步。
3. 挑一处语法讲给自己听：为什么这么写？换个写法还能不能做，区别在哪里？
4. 最后跑一下 lab 模式的测试。如果有列表、字典或状态，再看看原数据有没有被你不小心改掉。

## 接着往哪一节走

[项目说明](../../README.md) · [学习路线](../../ROADMAP.md) · [上一节](../12_rag/README.md) · [下一节](../14_mini_core/README.md)
