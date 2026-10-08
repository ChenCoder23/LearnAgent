# 04 · 迭代器、生成器、上下文与异常：语法与设计思路

这一节，咱们先从“迭代协议把数据来源和处理方式分开”聊起。先理解 Python 的规则和设计思路，再看它们能怎么用。你可以边读边运行小例子，别急着背结论。

咱们先把语言本身讲明白：语法怎么写、代码为什么这样工作、设计上有什么取舍。后面再把这些原理和本节实验联系起来，不按题目挨个拆答案。

## 先聊 Python 的语法和设计思路

这一部分先不看题。咱们从语言规则讲起，用小例子看看它为什么这样工作，再聊这种设计带来的方便和需要留意的地方。后面回到 lab，你就能把代码和这些原理对上。

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

### 推导式是在表达转换，生成器是在推迟计算

你写一段“遍历、判断、把转换结果放进去”的循环，经常可以写成推导式。它把“结果长什么样”放在前面，适合简短的数据转换。逻辑复杂、有很多副作用时，普通 for 循环更方便读和调试。

```python
values = [1, 2, 3, 4]
result = [x * 2 for x in values if x % 2 == 0]
assert result == [4, 8]
lazy = (x * 2 for x in values)
assert next(lazy) == 2
assert list(lazy) == [4, 6, 8]
```

方括号版本马上构造列表，圆括号版本得到生成器，等你来取值时才逐个计算。生成器通常只能走一遍，已经取过的不会自动再来。这是用计算时机和可重复遍历，换取较低的内存占用。别把列表推导式拿来只做打印之类的副作用，那个新建列表并没有用。

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

### with 把“打开—使用—收尾”放到一个结构里

锁要释放，文件要关闭，事务要提交或回滚。光靠每个调用者记得写清理代码不太可靠，Python 用上下文管理协议把这套生命周期收在 with 里。

```python
from contextlib import contextmanager

@contextmanager
def record(events):
    events.append("enter")
    try:
        yield events
    finally:
        events.append("exit")

events = []
with record(events) as current:
    current.append("work")
assert events == ["enter", "work", "exit"]
```

类写法中 __enter__ 的返回值交给 as 后的变量，__exit__ 收到异常信息并清理；返回真值会压制异常。contextmanager 则让你用一个生成器表达同样的过程，yield 前是进入，yield 后是退出，块内异常会送回暂停位置。

with 保证按协议退出，不自动保证持久性、线程安全或业务回滚。那些能力仍取决于上下文对象的实现。async with 类似，只是进入和退出也可以异步等待。

## 原理明白了，再看看这章会怎样用到它们

### 迭代协议

__iter__ 返回迭代器，__next__ 返回下一项，耗尽抛 StopIteration。Countdown 是一次性迭代器；take 不能先把无限序列转成列表。

### 惰性生成

含 yield 的函数返回生成器，实际执行延后到迭代时。sliding_window 维护长度 k 的缓冲，read_in_batches 分批产出，pipe 逐层组合可迭代对象。

### 上下文管理

__enter__ 的返回值绑定到 with 的 as 变量；__exit__ 负责清理。返回 True 会压制异常，Timer 必须让异常继续传播。contextmanager 用 yield 分隔进入与退出。

### 事务与异常链

transaction 进入前保存快照，异常时恢复状态。raise BusinessError(...) from error 把底层异常留在 __cause__，让业务含义与排错根因都可见。

### 控制流与双向生成器

try 成功才进 else，finally 无论成败都会执行。suppress 只压制指定异常；running_average 要先 next 预热，再用 send 把数字送到 yield 表达式。

## 顺着这章，还能多理解一点什么

流式读取减少峰值内存，适合日志、数据导入和模型片段输出。内存快照事务只是教学模型，不具备数据库隔离或持久化能力。

## 先看一小段代码，把语法拆开聊

```python
from contextlib import contextmanager

@contextmanager
def mark(events):
    events.append("enter")
    try:
        yield events
    finally:
        events.append("exit")
```

yield 暂停函数并把控制权交出；with 结束或抛异常时恢复执行退出部分。finally 应承担清理，不应随意 return 以免覆盖原结果或异常。

顺便认一下题目里常见的注解：`list[str]` 是“里面放字符串的列表”，`str | None` 是“字符串或者空值”，`->` 后面写返回什么类型。它们主要是在说明接口，不会替你检查或转换输入。`from __future__ import annotations` 则让注解暂时不求值，第 16 章会用到这个细节。

## 卡住了，先看看这些地方

- 不要对无限迭代器直接 list()。
- 生成器的参数校验可能在开始迭代时才触发。
- 回滚后仍应把异常抛出，不能把失败伪装成成功。

报错时，先去看失败测试里的 assert 或 pytest.raises：它到底希望得到什么？再回头检查类型、边界和返回值。NotImplementedError 通常是还有一处没写完，ImportError 则先去查环境和依赖。

想确认是不是自己的实现出了问题，可以暂时跑一下参考答案。下面用 finally 把模式切回 lab，省得下次不小心检查了答案，却以为自己做完了。

```powershell
$env:LEARN_TARGET = "solutions"
try {
    uv run pytest tests/test_04_iter_gen_exc.py -v
} finally {
    $env:LEARN_TARGET = "lab"
}
```

## 先打开哪些文件，怎么跑起来

- [练习文件](lab.py)：填写实现，保留函数名与签名。
- [参考实现](solutions.py)：卡住后对照，理解后合上重写。
- [验收测试](../../tests/test_04_iter_gen_exc.py)：核对准确输出、错误路径和边界。

打开仓库根目录下的 PowerShell，跑下面这两行。第一行是提醒程序：这次检查你写的 lab，别误跑参考答案。

```powershell
$env:LEARN_TARGET = "lab"
uv run pytest tests/test_04_iter_gen_exc.py -v
```

想只看一道题，就在命令后面加 `-k 关键词`，关键词可以从链接里的测试文件名和函数名里挑。要是看到 SKIPPED，那是这项没跑，不是做对了；先看看是不是少装了依赖。

## 做完了，试着给自己讲一遍

1. 先合上答案，说说每个函数或类吃进去什么、交回来什么，遇到什么会报错。
2. 挑一个边界例子，比如空输入或刚好卡在阈值上，自己走一遍每一步。
3. 挑一处语法讲给自己听：为什么这么写？换个写法还能不能做，区别在哪里？
4. 最后跑一下 lab 模式的测试。如果有列表、字典或状态，再看看原数据有没有被你不小心改掉。

## 接着往哪一节走

[项目说明](../../README.md) · [学习路线](../../ROADMAP.md) · [上一节](../03_oop/README.md) · [下一节](../05_typing_log/README.md)
