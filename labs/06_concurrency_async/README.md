# 06 · 线程、队列与 asyncio：语法与设计思路

这一节，咱们先从“并发设计先问：谁在共享状态，谁负责等待结束”聊起。先理解 Python 的规则和设计思路，再看它们能怎么用。你可以边读边运行小例子，别急着背结论。

咱们先把语言本身讲明白：语法怎么写、代码为什么这样工作、设计上有什么取舍。后面再把这些原理和本节实验联系起来，不按题目挨个拆答案。

## 先聊 Python 的语法和设计思路

这一部分先不看题。咱们从语言规则讲起，用小例子看看它为什么这样工作，再聊这种设计带来的方便和需要留意的地方。后面回到 lab，你就能把代码和这些原理对上。

### 并发设计先问：谁在共享状态，谁负责等待结束

并发是多个任务的进展交错发生，并行是同一时刻真的有多个任务在执行。线程、进程、协程各有成本和共享方式，不是选一个名字就能保证更快。

传统 CPython 的 GIL 会限制 Python 字节码的线程并行，但它不是你业务数据的事务锁。`value += 1` 这类读、计算、写回操作，应该按完整业务步骤保护。I/O 等待适合线程或异步，CPU 工作则要考虑进程或能释放 GIL 的计算实现；具体还要测。

```python
import threading

lock = threading.Lock()
counter = 0
with lock:
    counter += 1
assert counter == 1
```

队列让生产者和消费者不用直接抢同一份裸列表。线程 start 后，主线程通常还要 join 等待；线程池也要消费结果或等待关闭。锁的范围太大影响吞吐，太小保护不住不变量，所以先说清楚哪些数据必须一起保持一致。

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

### 线程与等待

ThreadPoolExecutor 把等待任务交给多个线程，map 的结果需要消费完才代表工作完成。perf_counter 测耗时；单次时间不是稳定性能结论。

### 共享状态与队列

锁保护读-改-写整个临界区，Queue 安全传递任务，线程 start 后要 join 等待结束。具体是否复现丢失更新取决于调度和解释器，不能靠 GIL 代替锁。

### 协程与并发

async def 调用得到协程，await 等待可等待对象。gather 同时组织多个任务，返回结果顺序与传入顺序相同；asyncio.sleep 让出事件循环。

### 限流与超时

Semaphore 限制同时进入的任务数，async with 确保退出时释放。峰值计数要在受控区域内统计，并用 finally 减回；wait_for 限定等待时间。

### 阻塞适配与异步重试

run_in_executor 把阻塞函数放到线程池，避免卡住事件循环。async_retry 的等待用 await asyncio.sleep；gather(return_exceptions=True) 把错误作为结果收集。

## 顺着这章，还能多理解一点什么

传统 CPython 的 GIL 限制 Python 字节码线程并行；CPU 密集工作通常考虑进程，I/O 工作可用线程或协程。异步是协作调度，await 之间的阻塞代码仍会卡住整个循环。

## 先看一小段代码，把语法拆开聊

```python
import asyncio

async def example():
    async def one(value):
        await asyncio.sleep(0)
        return value * 2
    return await asyncio.gather(one(1), one(2))

assert asyncio.run(example()) == [2, 4]
```

asyncio.run 是同步程序的事件循环入口；已有运行中事件循环时应直接 await。协程不是调用后立即完成的普通函数。

顺便认一下题目里常见的注解：`list[str]` 是“里面放字符串的列表”，`str | None` 是“字符串或者空值”，`->` 后面写返回什么类型。它们主要是在说明接口，不会替你检查或转换输入。`from __future__ import annotations` 则让注解暂时不求值，第 16 章会用到这个细节。

## 卡住了，先看看这些地方

- 限流参数应为正数，0 个许可会使任务无法进入。
- 异步代码内 time.sleep 会阻塞循环。
- 成功结果与异常对象要分别收集，不能把异常当文本成功结果。

报错时，先去看失败测试里的 assert 或 pytest.raises：它到底希望得到什么？再回头检查类型、边界和返回值。NotImplementedError 通常是还有一处没写完，ImportError 则先去查环境和依赖。

想确认是不是自己的实现出了问题，可以暂时跑一下参考答案。下面用 finally 把模式切回 lab，省得下次不小心检查了答案，却以为自己做完了。

```powershell
$env:LEARN_TARGET = "solutions"
try {
    uv run pytest tests/test_06_concurrency_async.py -v
} finally {
    $env:LEARN_TARGET = "lab"
}
```

## 先打开哪些文件，怎么跑起来

- [练习文件](lab.py)：填写实现，保留函数名与签名。
- [参考实现](solutions.py)：卡住后对照，理解后合上重写。
- [验收测试](../../tests/test_06_concurrency_async.py)：核对准确输出、错误路径和边界。

打开仓库根目录下的 PowerShell，跑下面这两行。第一行是提醒程序：这次检查你写的 lab，别误跑参考答案。

```powershell
$env:LEARN_TARGET = "lab"
uv run pytest tests/test_06_concurrency_async.py -v
```

想只看一道题，就在命令后面加 `-k 关键词`，关键词可以从链接里的测试文件名和函数名里挑。要是看到 SKIPPED，那是这项没跑，不是做对了；先看看是不是少装了依赖。

## 做完了，试着给自己讲一遍

1. 先合上答案，说说每个函数或类吃进去什么、交回来什么，遇到什么会报错。
2. 挑一个边界例子，比如空输入或刚好卡在阈值上，自己走一遍每一步。
3. 挑一处语法讲给自己听：为什么这么写？换个写法还能不能做，区别在哪里？
4. 最后跑一下 lab 模式的测试。如果有列表、字典或状态，再看看原数据有没有被你不小心改掉。

## 接着往哪一节走

[项目说明](../../README.md) · [学习路线](../../ROADMAP.md) · [上一节](../05_typing_log/README.md) · [下一节](../07_internals/README.md)
