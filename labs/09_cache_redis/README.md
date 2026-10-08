# 09 · TTL、缓存策略、锁与幂等：语法与设计思路

这一节，咱们先从“选容器时，先看你要顺序、查找，还是映射”聊起。先理解 Python 的规则和设计思路，再看它们能怎么用。你可以边读边运行小例子，别急着背结论。

咱们先把语言本身讲明白：语法怎么写、代码为什么这样工作、设计上有什么取舍。后面再把这些原理和本节实验联系起来，不按题目挨个拆答案。

## 先聊 Python 的语法和设计思路

这一部分先不看题。咱们从语言规则讲起，用小例子看看它为什么这样工作，再聊这种设计带来的方便和需要留意的地方。后面回到 lab，你就能把代码和这些原理对上。

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

### 存储与时间

MemoryStore 记录值与过期时间；get 时惰性清除过期键，incr 不应重置已有 TTL。注入 clock 让测试可以直接推进时间。

### 缓存三类问题

穿透是不断查询不存在的数据，可用较短 TTL 的空值哨兵；击穿是热点过期时同时回源，可用 single_flight；雪崩是大量键同时过期，可用 TTL 抖动。

### 锁的归属

SET NX EX 同时表达不存在才写和过期时间；每次持有锁用唯一 token。释放要比较 token 后删除，防止过期旧持有者删掉新持有者的锁。

### 原子操作与 Lua

真实 Redis 上分开的 GET 与 DEL 存在竞态，释放脚本把比较和删除放在同一次原子执行中；KEYS[1] 是锁键，ARGV[1] 是持有者 token。

### 幂等与限流

idempotent 存首次结果供重复请求回放；rate_limit 用固定窗口计数，第一次 INCR 设置窗口 TTL。它们都是教学算法，不自动解决所有跨进程竞态。

## 顺着这章，还能多理解一点什么

锁租期到期后 loader 仍可能运行，single_flight 的等待者耗尽重试也会直接回源，所以不是绝对一次执行。固定窗口在窗口交界可形成突发；生产可比较滑动窗口或令牌桶。

## 先看一小段代码，把语法拆开聊

```python
release_script = """
if redis.call("GET", KEYS[1]) == ARGV[1] then
    return redis.call("DEL", KEYS[1])
end
return 0
"""
```

三引号保存多行字符串，内容是 Lua 而不是 Python。Lua 使用 then/end 包围条件体，== 比较 token，redis.call 调用 Redis 命令。

顺便认一下题目里常见的注解：`list[str]` 是“里面放字符串的列表”，`str | None` 是“字符串或者空值”，`->` 后面写返回什么类型。它们主要是在说明接口，不会替你检查或转换输入。`from __future__ import annotations` 则让注解暂时不求值，第 16 章会用到这个细节。

## 卡住了，先看看这些地方

- 缓存命中值可以是 0、False 或空列表，不要误判未命中。
- NULL_SENTINEL 区分已缓存空值和没有缓存。
- 真实分布式幂等需要原子抢占或数据库约束，单纯查询再写不够。

报错时，先去看失败测试里的 assert 或 pytest.raises：它到底希望得到什么？再回头检查类型、边界和返回值。NotImplementedError 通常是还有一处没写完，ImportError 则先去查环境和依赖。

想确认是不是自己的实现出了问题，可以暂时跑一下参考答案。下面用 finally 把模式切回 lab，省得下次不小心检查了答案，却以为自己做完了。

```powershell
$env:LEARN_TARGET = "solutions"
try {
    uv run pytest tests/test_09_cache_redis.py -v
} finally {
    $env:LEARN_TARGET = "lab"
}
```

## 先打开哪些文件，怎么跑起来

- [练习文件](lab.py)：填写实现，保留函数名与签名。
- [参考实现](solutions.py)：卡住后对照，理解后合上重写。
- [验收测试](../../tests/test_09_cache_redis.py)：核对准确输出、错误路径和边界。

打开仓库根目录下的 PowerShell，跑下面这两行。第一行是提醒程序：这次检查你写的 lab，别误跑参考答案。

```powershell
$env:LEARN_TARGET = "lab"
uv run pytest tests/test_09_cache_redis.py -v
```

想只看一道题，就在命令后面加 `-k 关键词`，关键词可以从链接里的测试文件名和函数名里挑。要是看到 SKIPPED，那是这项没跑，不是做对了；先看看是不是少装了依赖。

## 做完了，试着给自己讲一遍

1. 先合上答案，说说每个函数或类吃进去什么、交回来什么，遇到什么会报错。
2. 挑一个边界例子，比如空输入或刚好卡在阈值上，自己走一遍每一步。
3. 挑一处语法讲给自己听：为什么这么写？换个写法还能不能做，区别在哪里？
4. 最后跑一下 lab 模式的测试。如果有列表、字典或状态，再看看原数据有没有被你不小心改掉。

## 接着往哪一节走

[项目说明](../../README.md) · [学习路线](../../ROADMAP.md) · [上一节](../08_fastapi_sql/README.md) · [下一节](../10_llm_prompt_parser/README.md)
