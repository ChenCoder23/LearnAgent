# 11 · Runnable、LCEL 与组合链：语法与设计思路

这一节，咱们先从“函数把计算过程变成一个可以传递的对象”聊起。先理解 Python 的规则和设计思路，再看它们能怎么用。你可以边读边运行小例子，别急着背结论。

咱们先把语言本身讲明白：语法怎么写、代码为什么这样工作、设计上有什么取舍。后面再把这些原理和本节实验联系起来，不按题目挨个拆答案。

## 先聊 Python 的语法和设计思路

这一部分先不看题。咱们从语言规则讲起，用小例子看看它为什么这样工作，再聊这种设计带来的方便和需要留意的地方。后面回到 lab，你就能把代码和这些原理对上。

### 函数把计算过程变成一个可以传递的对象

写 `def` 时，你是在创建一个函数对象，再把名字绑定到它。函数体不会因为定义完就立刻执行，得等调用。括号里的参数是在说明“调用时把哪些值交进来”，`return` 则是在说明“这次把什么结果交出去”。

函数在 Python 里也是普通对象，可以赋给另一个名字、放进列表、作为参数传进去，也可以作为返回值。语言不用额外发明一种“回调类型语法”，就能让排序、事件处理、数据转换使用同样的机制。

```python
def double(value):
    return value * 2

operation = double
assert operation(3) == 6
assert list(map(operation, [1, 2])) == [2, 4]
```

`operation = double` 传的是函数本身，`operation = double(3)` 传的是执行结果，这两句差别很大。没有写 return 的函数会返回 None。print 只是输出到屏幕，不能拿它代替函数返回值；把计算和显示分开，函数才更容易复用和测试。

### Python 喜欢按能力合作：协议和鸭子类型

如果一个对象能完成你需要的操作，你不一定非得先问它属于哪个具体类。比如 for 只需要对象能提供迭代，with 只需要上下文管理协议，调用表达式只需要对象可调用。这就是按能力合作的思路。

```python
class Doubler:
    def __call__(self, value):
        return value * 2

def apply(operation, value):
    return operation(value)

assert apply(Doubler(), 3) == 6
assert apply(lambda x: x + 1, 3) == 4
```

特殊方法让自己的对象接入现成语法：__call__ 接入调用，__iter__ 接入迭代，__or__ 接入 |。这样使用者可以保持同一套写法，不用为每个实现发明新入口。

鸭子类型让组件替换灵活，但缺方法时往往要运行到那一步才发现。typing.Protocol 能把需要哪些方法写成静态接口，ABC 则能通过抽象方法限制实例创建；它们解决的环节不同，都不是万能的运行时数据校验。

### 组合的关键是接口小，数据怎么走要明确

假设每个处理组件都支持 invoke(value)，你就能把它们串起来：前一个的输出交给后一个。语言没有内置一个“业务流水线”，但一等函数、对象协议和运算符重载足够让你搭起来。

```python
class Stage:
    def __init__(self, func):
        self.func = func
    def invoke(self, value):
        return self.func(value)
    def __or__(self, other):
        return Stage(lambda x: other.invoke(self.invoke(x)))

chain = Stage(lambda x: x + 1) | Stage(lambda x: x * 2)
assert chain.invoke(3) == 8
```

| 原本是一个运算符，这里通过 __or__ 让它表达组合。构建 chain 时只是保存关系，invoke 时才真正运行，这让构建和执行可以分开。运算符重载最好保持含义直观，别让一句简单语法偷偷做很难预测的事情。

接口统一不代表数据形状统一。某段输出字典，下一段却要消息列表，照样接不上。组合前先写清每一步输入输出，适配器负责转换。每项重试、分支、映射也可以包装成同一个接口，能力靠组合扩展，而不是无限增加继承层数。

### async/await 是协作等待，不是自动开线程

调用 async def 函数会得到协程对象。把它 await，或者安排成任务，它才进入执行流程。遇到需要等待的可等待对象时，事件循环可以转去推进其他任务；这就是很多 I/O 等待能重叠起来的原因。

```python
import asyncio

async def one(value):
    await asyncio.sleep(0)
    return value * 2

async def main():
    return await asyncio.gather(one(1), one(2))

assert asyncio.run(main()) == [2, 4]
```

gather 组织多个可等待对象，结果按输入顺序返回。await 不是“保证立刻切换线程”，协程里一大段 CPU 运算或 time.sleep 仍会挡住事件循环。旧的阻塞函数可以交给执行器，但线程工作也不是一句 await 就能随意中止。

Semaphore 控制同时做事的数量，Lock 保护共享状态，两者目的不同。超时、取消和异常时都得归还资源，所以 async with 和 try/finally 很重要。异步提升的是等待任务的处理能力，不会凭空减少计算工作量。

## 原理明白了，再看看这章会怎样用到它们

### 串行组合

prompt | model | parser 从左到右传递结果；invoke 执行一项，batch 执行一批，ainvoke 提供异步调用接口。Python 的 | 在这里由组件重载实现。

### 并行与透传

RunnableParallel 把同一输入给多个分支，输出按分支名组装为字典；RunnablePassthrough 原样传递当前输入。字典输入需取 question 字段，不能误把整字典当问题文本。

### 条件分支

RunnableBranch 选择条件成立的分支，否则走默认分支。route_by_length 的阈值是大于 10；LONG/SHORT 系统提示让假模型能验证路由。

### 检索链

检索器产生文档，format_docs 拼上下文，另一路保留问题，最终合并成模板输入。先确认本题 RAG 链输入是问题字符串，与第 15 章的字典输入不同。

### 配置与容错

config 中 tags 传给内部可执行组件；with_retry 重跑同一组件，with_fallbacks 改跑备用组件。包装的 lambda 需要接收 config 才能观察配置传播。

## 顺着这章，还能多理解一点什么

并行是数据流分叉的结构，同时也可能涉及并发执行；第 14 章教学 RunnableParallel 先用顺序实现。链能否完整流式输出取决于所有组件的流式能力。

## 先看一小段代码，把语法拆开聊

```python
from langchain_core.runnables import RunnableLambda, RunnableParallel

double = RunnableLambda(lambda value: value * 2)
chain = RunnableParallel({"double": double, "original": RunnableLambda(lambda x: x)})
assert chain.invoke(3) == {"double": 6, "original": 3}
```

lambda 定义短函数；字典键给分支命名。invoke(3) 会把 3 分别交给两条分支，最终返回包含两份结果的字典。

顺便认一下题目里常见的注解：`list[str]` 是“里面放字符串的列表”，`str | None` 是“字符串或者空值”，`->` 后面写返回什么类型。它们主要是在说明接口，不会替你检查或转换输入。`from __future__ import annotations` 则让注解暂时不求值，第 16 章会用到这个细节。

## 卡住了，先看看这些地方

- batch 输出应保持输入顺序。
- 长度恰好 10 走 short 分支。
- with_retry 返回新 Runnable，需实际执行它才能观察重试。

报错时，先去看失败测试里的 assert 或 pytest.raises：它到底希望得到什么？再回头检查类型、边界和返回值。NotImplementedError 通常是还有一处没写完，ImportError 则先去查环境和依赖。

想确认是不是自己的实现出了问题，可以暂时跑一下参考答案。下面用 finally 把模式切回 lab，省得下次不小心检查了答案，却以为自己做完了。

```powershell
$env:LEARN_TARGET = "solutions"
try {
    uv run pytest tests/test_11_lcel_runnable.py -v
} finally {
    $env:LEARN_TARGET = "lab"
}
```

## 先打开哪些文件，怎么跑起来

- [练习文件](lab.py)：填写实现，保留函数名与签名。
- [参考实现](solutions.py)：卡住后对照，理解后合上重写。
- [验收测试](../../tests/test_11_lcel_runnable.py)：核对准确输出、错误路径和边界。

打开仓库根目录下的 PowerShell，跑下面这两行。第一行是提醒程序：这次检查你写的 lab，别误跑参考答案。

```powershell
$env:LEARN_TARGET = "lab"
uv run pytest tests/test_11_lcel_runnable.py -v
```

想只看一道题，就在命令后面加 `-k 关键词`，关键词可以从链接里的测试文件名和函数名里挑。要是看到 SKIPPED，那是这项没跑，不是做对了；先看看是不是少装了依赖。

## 做完了，试着给自己讲一遍

1. 先合上答案，说说每个函数或类吃进去什么、交回来什么，遇到什么会报错。
2. 挑一个边界例子，比如空输入或刚好卡在阈值上，自己走一遍每一步。
3. 挑一处语法讲给自己听：为什么这么写？换个写法还能不能做，区别在哪里？
4. 最后跑一下 lab 模式的测试。如果有列表、字典或状态，再看看原数据有没有被你不小心改掉。

## 接着往哪一节走

[项目说明](../../README.md) · [学习路线](../../ROADMAP.md) · [上一节](../10_llm_prompt_parser/README.md) · [下一节](../12_rag/README.md)
