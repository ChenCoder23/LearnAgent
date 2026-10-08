# 14 · 手写 Runnable、Prompt、Parser 与模型：语法与设计思路

这一节，咱们先从“Python 喜欢按能力合作：协议和鸭子类型”聊起。先理解 Python 的规则和设计思路，再看它们能怎么用。你可以边读边运行小例子，别急着背结论。

咱们先把语言本身讲明白：语法怎么写、代码为什么这样工作、设计上有什么取舍。后面再把这些原理和本节实验联系起来，不按题目挨个拆答案。

## 先聊 Python 的语法和设计思路

这一部分先不看题。咱们从语言规则讲起，用小例子看看它为什么这样工作，再聊这种设计带来的方便和需要留意的地方。后面回到 lab，你就能把代码和这些原理对上。

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

### 作用域和闭包：函数怎么记住外层环境

读一个名字时，Python 通常从当前局部作用域往外找，再找模块全局和内置名字。内层函数用到外层变量，就形成了闭包；外层调用结束了，那些被内层函数需要的绑定仍然能继续存在。

```python
def counter():
    value = 0
    def next_value():
        nonlocal value
        value += 1
        return value
    return next_value

c = counter()
assert (c(), c()) == (1, 2)
```

nonlocal 表示这次重新赋值要改外层那个绑定。只是读外层变量不用写它；修改外层列表的内容也不一定需要，因为那没有重新绑定名字。

闭包捕获的是绑定，不是自动给每次循环拍一张数值快照。`[lambda: i for i in range(3)]` 里的函数等到调用时才看 i，所以都看到最后那个值。默认参数 `lambda i=i: i`、工厂函数或 partial 都可以把当前值固定下来。这种机制让闭包能共享状态，也要求你留意状态到底是谁的。

### 继承沿 MRO 走，组合按职责接起来

super() 不是“点名找我的某个父类”，而是按当前对象的 MRO 接着往后找。在多继承里，这能让多个小配件各做一部分初始化，再把剩余参数转交下一环，避免同一个基类被重复初始化。

```python
class Base:
    def greet(self):
        return ["base"]

class Extra(Base):
    def greet(self):
        return ["extra", *super().greet()]

assert Extra().greet() == ["extra", "base"]
```

Mixin 常用来提供一小块可复用能力，不过参与协作的方法要遵守共同的参数与调用约定。有人漏了 super，后面的环节就接不上。

组合则是让对象持有其他组件，明确调用它们。用继承表示“它是一种什么”，用组合表达“它由什么能力搭成”，通常更容易分清关系。像处理流水线，阶段不同但共享执行接口，用组合就不需要为每种阶段排列创建一个新子类。

## 原理明白了，再看看这章会怎样用到它们

### 消息归一化

Message 保存 role/content，to_messages 统一字符串、单条消息和嵌套序列；不支持的类型抛 TypeError。模型调用前统一输入可以减少下游分支。

### 运算符与适配

Runnable.__or__ 构造 RunnableSequence，coerce_runnable 将函数包装成 RunnableLambda，将常量包装成忽略输入的组件；构建链不应提前执行它。

### 串行与分叉

Sequence 每步接收前一步结果并传 config；Parallel 将同一输入送到各分支再组装字典，本实现按顺序执行分支。map 是把同一组件应用到每个元素。

### 流式与包装

默认 stream 只 yield 一次 invoke 结果；Sequence 先执行前面步骤，再 yield from 最后一步。重试和降级用闭包包装目标，不必修改原对象。

### 模板与模型

ChatPromptTemplate 用 format(**payload) 渲染消息；StrOutputParser 统一提取文本。BaseChatModel 负责归一化与 seen 记录，FakeChatModel 按剧本提供确定性回复。

## 顺着这章，还能多理解一点什么

本章的 Runnable 是教学子集，不等价于完整 LangChain：没有端到端 chunk 转换、复杂回调、全面签名适配或真正并行调度。理解职责边界比复刻所有 API 更重要。

## 先看一小段代码，把语法拆开聊

```python
class Stage:
    def __init__(self, func):
        self.func = func
    def __call__(self, value):
        return self.func(value)
    def __or__(self, other):
        return Stage(lambda value: other(self(value)))

assert (Stage(lambda x: x + 1) | Stage(lambda x: x * 2))(3) == 8
```

__or__ 重载 |，__call__ 让对象可以调用。lambda 捕获当前两段组件，真正计算延迟到组合对象收到输入时。

顺便认一下题目里常见的注解：`list[str]` 是“里面放字符串的列表”，`str | None` 是“字符串或者空值”，`->` 后面写返回什么类型。它们主要是在说明接口，不会替你检查或转换输入。`from __future__ import annotations` 则让注解暂时不求值，第 16 章会用到这个细节。

## 卡住了，先看看这些地方

- invoke 和 stream 返回形状不同，stream 应可迭代。
- Sequence 在每一步都要传 config，不能只传最后一步。
- 参考 FakeChatModel 剧本耗尽后返回提示文字，不会自动循环剧本。

报错时，先去看失败测试里的 assert 或 pytest.raises：它到底希望得到什么？再回头检查类型、边界和返回值。NotImplementedError 通常是还有一处没写完，ImportError 则先去查环境和依赖。

想确认是不是自己的实现出了问题，可以暂时跑一下参考答案。下面用 finally 把模式切回 lab，省得下次不小心检查了答案，却以为自己做完了。

```powershell
$env:LEARN_TARGET = "solutions"
try {
    uv run pytest tests/test_14_mini_core.py -v
} finally {
    $env:LEARN_TARGET = "lab"
}
```

## 先打开哪些文件，怎么跑起来

- [练习文件](lab.py)：填写实现，保留函数名与签名。
- [参考实现](solutions.py)：卡住后对照，理解后合上重写。
- [验收测试](../../tests/test_14_mini_core.py)：核对准确输出、错误路径和边界。

打开仓库根目录下的 PowerShell，跑下面这两行。第一行是提醒程序：这次检查你写的 lab，别误跑参考答案。

```powershell
$env:LEARN_TARGET = "lab"
uv run pytest tests/test_14_mini_core.py -v
```

想只看一道题，就在命令后面加 `-k 关键词`，关键词可以从链接里的测试文件名和函数名里挑。要是看到 SKIPPED，那是这项没跑，不是做对了；先看看是不是少装了依赖。

## 做完了，试着给自己讲一遍

1. 先合上答案，说说每个函数或类吃进去什么、交回来什么，遇到什么会报错。
2. 挑一个边界例子，比如空输入或刚好卡在阈值上，自己走一遍每一步。
3. 挑一处语法讲给自己听：为什么这么写？换个写法还能不能做，区别在哪里？
4. 最后跑一下 lab 模式的测试。如果有列表、字典或状态，再看看原数据有没有被你不小心改掉。

## 接着往哪一节走

[项目说明](../../README.md) · [学习路线](../../ROADMAP.md) · [上一节](../13_agent_tools/README.md) · [下一节](../15_mini_rag/README.md)
