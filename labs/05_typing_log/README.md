# 05 · 类型协议、分页、文件与日志：语法与设计思路

这一节，咱们先从“类型注解是在沟通接口，运行时校验是另一件事”聊起。先理解 Python 的规则和设计思路，再看它们能怎么用。你可以边读边运行小例子，别急着背结论。

咱们先把语言本身讲明白：语法怎么写、代码为什么这样工作、设计上有什么取舍。后面再把这些原理和本节实验联系起来，不按题目挨个拆答案。

## 先聊 Python 的语法和设计思路

这一部分先不看题。咱们从语言规则讲起，用小例子看看它为什么这样工作，再聊这种设计带来的方便和需要留意的地方。后面回到 lab，你就能把代码和这些原理对上。

### 类型注解是在沟通接口，运行时校验是另一件事

`name: str`、`list[int]`、`-> bool` 都是在说明这段代码希望怎样被使用。普通 Python 函数不会因为写了注解就自动挡住错误类型，类型检查器能提前找一部分问题，运行时约束还要靠显式检查或校验库。

```python
def echo(value: int) -> int:
    return value

assert echo("text") == "text"  # 运行时不会因为注解自动拒绝
```

泛型描述的是类型之间的关系：Page[T] 里 items 是 T，映射到 U 后变成 Page[U]，而不是把分页信息全丢掉。Protocol 写出组件需要具备的方法，让接口和具体存储实现分开。

本仓库用 future annotations 延迟求值注解，因此反射时可能看到字符串形式的注解。需要拿到 int、float 等实际类型对象时，用 get_type_hints 解析。类型注解不是完整输入 schema：范围、必填、长度、字段间关系还需要另外描述和验证。

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

### 可变性、默认参数和拷贝其实是一条线

有了“名字指向对象”这个模型，再看默认参数就容易了。默认值是在执行 def 时准备好的，不是每次调用都重新算。写 `items=[]`，后续省略这个参数的调用就会反复拿到同一个列表。

```python
def append_new(value, items=None):
    result = list(items) if items is not None else []
    result.append(value)
    return result

source = [[1]]
copy_outer = list(source)
copy_outer[0].append(2)
assert source == [[1, 2]]
assert append_new("x") == ["x"]
assert append_new("y") == ["y"]
```

用 None 作为“没传”的记号，函数里再造列表，就能隔开不同调用。可这里的 list(source) 只复制外层，内层列表还是共享的。需要连嵌套对象一起隔开时，可以用 deepcopy；代价是更多复制工作，也不适合盲目复制文件、连接等资源。

接口设计时最好提前说清楚：函数会原地修改输入，还是返回一份新结果？两种方式都能用，混着用却不说明，调用者就很容易踩坑。

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

### 泛型分页

Page[T] 表示 items 的元素类型，map_page 将 T 映射为另一类型并保留分页元数据。页码从 1 开始，offset=(page-1)*size，总页数用向上取整。

### 结构协议

Protocol 描述调用方所需方法；实现不必显式继承协议，只要结构满足。sync_all 依赖 Repository 接口，InMemoryRepo 用拷贝避免调用者绕过 save 修改存储。

### 显式校验

validate_user 按 name、age、email 顺序收集错误；bool 虽是 int 子类，本题不应接受为年龄。类型注解不会完成这些运行时校验。

### 原子替换

write_json_atomic 在目标同目录写临时文件再 os.replace；UTF-8 与 ensure_ascii=False 保持中文可读。它解决读者看到半个文件的问题，不等于多写者协调或断电持久性。

### 上下文日志

ContextVar 把 request_id 绑定到执行上下文，set 返回 token 可用于 reset。JsonFormatter 生成一行 JSON，logger 复用且只挂一个 handler，propagate=False 避免重复输出。

## 顺着这章，还能多理解一点什么

Pydantic 的模型校验会在第 08 章实际使用；本章 validate_user 刻意手写校验。日志自定义字段应避免覆盖 ts、level 等核心字段，文件并发写入还需独立临时文件与协调策略。

## 先看一小段代码，把语法拆开聊

```python
from contextvars import ContextVar

request_id = ContextVar("request_id", default="-")
token = request_id.set("req-001")
try:
    assert request_id.get() == "req-001"
finally:
    request_id.reset(token)
```

set 返回的是恢复凭据 token；reset 恢复此前值，不是简单设为默认值。try/finally 确保请求处理失败时也还原上下文。

顺便认一下题目里常见的注解：`list[str]` 是“里面放字符串的列表”，`str | None` 是“字符串或者空值”，`->` 后面写返回什么类型。它们主要是在说明接口，不会替你检查或转换输入。`from __future__ import annotations` 则让注解暂时不求值，第 16 章会用到这个细节。

## 卡住了，先看看这些地方

- 超范围页返回空 items，但 total 不应变成 0。
- 重复 setup_json_logger 后不应出现重复日志。
- 读文件不存在时应保留 FileNotFoundError。

报错时，先去看失败测试里的 assert 或 pytest.raises：它到底希望得到什么？再回头检查类型、边界和返回值。NotImplementedError 通常是还有一处没写完，ImportError 则先去查环境和依赖。

想确认是不是自己的实现出了问题，可以暂时跑一下参考答案。下面用 finally 把模式切回 lab，省得下次不小心检查了答案，却以为自己做完了。

```powershell
$env:LEARN_TARGET = "solutions"
try {
    uv run pytest tests/test_05_typing_log.py -v
} finally {
    $env:LEARN_TARGET = "lab"
}
```

## 先打开哪些文件，怎么跑起来

- [练习文件](lab.py)：填写实现，保留函数名与签名。
- [参考实现](solutions.py)：卡住后对照，理解后合上重写。
- [验收测试](../../tests/test_05_typing_log.py)：核对准确输出、错误路径和边界。

打开仓库根目录下的 PowerShell，跑下面这两行。第一行是提醒程序：这次检查你写的 lab，别误跑参考答案。

```powershell
$env:LEARN_TARGET = "lab"
uv run pytest tests/test_05_typing_log.py -v
```

想只看一道题，就在命令后面加 `-k 关键词`，关键词可以从链接里的测试文件名和函数名里挑。要是看到 SKIPPED，那是这项没跑，不是做对了；先看看是不是少装了依赖。

## 做完了，试着给自己讲一遍

1. 先合上答案，说说每个函数或类吃进去什么、交回来什么，遇到什么会报错。
2. 挑一个边界例子，比如空输入或刚好卡在阈值上，自己走一遍每一步。
3. 挑一处语法讲给自己听：为什么这么写？换个写法还能不能做，区别在哪里？
4. 最后跑一下 lab 模式的测试。如果有列表、字典或状态，再看看原数据有没有被你不小心改掉。

## 接着往哪一节走

[项目说明](../../README.md) · [学习路线](../../ROADMAP.md) · [上一节](../04_iter_gen_exc/README.md) · [下一节](../06_concurrency_async/README.md)
