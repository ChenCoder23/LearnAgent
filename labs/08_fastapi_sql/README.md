# 08 · FastAPI、SQLAlchemy 与分层后端：语法与设计思路

这一节，咱们先从“对象组织状态，值对象则更关心“相等””聊起。先理解 Python 的规则和设计思路，再看它们能怎么用。你可以边读边运行小例子，别急着背结论。

咱们先把语言本身讲明白：语法怎么写、代码为什么这样工作、设计上有什么取舍。后面再把这些原理和本节实验联系起来，不按题目挨个拆答案。

## 先聊 Python 的语法和设计思路

这一部分先不看题。咱们从语言规则讲起，用小例子看看它为什么这样工作，再聊这种设计带来的方便和需要留意的地方。后面回到 lab，你就能把代码和这些原理对上。

### 对象组织状态，值对象则更关心“相等”

类把一组状态和相关操作放到一起，实例方法的 self 就是这次操作的对象。对象什么时候相等，要看你的语义：用户实体可能按 ID 比较，金额或坐标则通常按字段值比较。

如果你实现 __eq__，又希望对象能放进 set 或做 dict 键，还要一起考虑 __hash__：两个相等对象必须有相同哈希，键放进去之后影响哈希的字段应保持稳定。否则明明对象还在，查找却可能找不到。

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Point:
    x: int
    y: int

assert Point(1, 2) == Point(1, 2)
assert len({Point(1, 2), Point(1, 2)}) == 1
```

dataclass 替你生成常见方法，frozen 阻止正常属性赋值，不过不代表里面的所有可变字段都深度冻结。__slots__ 主要限制实例字段并节省实例字典开销，也不等于只读。遇到不支持的运算对象，可以返回 NotImplemented，让 Python 尝试另一侧的协议；它和抛 NotImplementedError 是两回事。

### 类型注解是在沟通接口，运行时校验是另一件事

`name: str`、`list[int]`、`-> bool` 都是在说明这段代码希望怎样被使用。普通 Python 函数不会因为写了注解就自动挡住错误类型，类型检查器能提前找一部分问题，运行时约束还要靠显式检查或校验库。

```python
def echo(value: int) -> int:
    return value

assert echo("text") == "text"  # 运行时不会因为注解自动拒绝
```

泛型描述的是类型之间的关系：Page[T] 里 items 是 T，映射到 U 后变成 Page[U]，而不是把分页信息全丢掉。Protocol 写出组件需要具备的方法，让接口和具体存储实现分开。

本仓库用 future annotations 延迟求值注解，因此反射时可能看到字符串形式的注解。需要拿到 int、float 等实际类型对象时，用 get_type_hints 解析。类型注解不是完整输入 schema：范围、必填、长度、字段间关系还需要另外描述和验证。

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

## 原理明白了，再看看这章会怎样用到它们

### ORM 与模型

DeclarativeBase 管理映射元数据，Mapped[T]/mapped_column 声明列；Article 是数据库对象，ArticleCreate/Update/Out 是接口模型，字段形状不能混为一谈。

### 会话与事务

engine 是数据库连接入口，sessionmaker 创建会话。session_scope 正常退出 commit，异常 rollback，最后 close；flush 发送变更并获得主键，不代表事务已提交。

### 查询与分页

select 构建语句，where 过滤，order_by 稳定排序，offset/limit 分页；总数 count 必须使用同样的 keyword 过滤条件。

### 业务与缓存

Cache-Aside 先读缓存，未命中读库并回填；更新或删除先提交数据库，再删除缓存。Service 输出 DTO，避免让关闭会话后的 ORM 延迟加载泄漏到 API。

### 路由与注入

FastAPI 的路由装饰器声明方法和路径，Depends 提供服务依赖，Query/Field 描述边界。创建返回 201，删除 204，找不到 404，标题冲突 409，输入错误 422。

## 顺着这章，还能多理解一点什么

查重再插入存在并发窗口，唯一约束才是数据库最终保障；生产服务还需捕获 IntegrityError 并转换错误。这里的内存缓存仅供单进程教学，不是跨进程一致性方案。

## 先看一小段代码，把语法拆开聊

```python
from sqlalchemy import select

# 假设 Article 和 session 来自本章初始化流程
statement = select(Article).order_by(Article.id).offset(0).limit(10)
# session.scalars(statement) 取出实体，而不是带实体的 Row 包装
```

链式方法逐步构建 SQL 语句；class 上的 Article.id 是 SQL 表达式入口，实例上的 article.id 才是具体字段值。本片段需已有数据库上下文。

顺便认一下题目里常见的注解：`list[str]` 是“里面放字符串的列表”，`str | None` 是“字符串或者空值”，`->` 后面写返回什么类型。它们主要是在说明接口，不会替你检查或转换输入。`from __future__ import annotations` 则让注解暂时不求值，第 16 章会用到这个细节。

## 卡住了，先看看这些地方

- 更新 tags=[] 表示清空；不能用 if payload.tags 判断是否提供值。
- 列表返回的 total 是过滤后的总数，不是当前页长度。
- Service 在各操作中创建会话；Depends 注入的 Service 本身可以复用。

报错时，先去看失败测试里的 assert 或 pytest.raises：它到底希望得到什么？再回头检查类型、边界和返回值。NotImplementedError 通常是还有一处没写完，ImportError 则先去查环境和依赖。

想确认是不是自己的实现出了问题，可以暂时跑一下参考答案。下面用 finally 把模式切回 lab，省得下次不小心检查了答案，却以为自己做完了。

```powershell
$env:LEARN_TARGET = "solutions"
try {
    uv run pytest tests/test_08_fastapi_sql.py -v
} finally {
    $env:LEARN_TARGET = "lab"
}
```

## 先打开哪些文件，怎么跑起来

- [练习文件](lab.py)：填写实现，保留函数名与签名。
- [参考实现](solutions.py)：卡住后对照，理解后合上重写。
- [验收测试](../../tests/test_08_fastapi_sql.py)：核对准确输出、错误路径和边界。

打开仓库根目录下的 PowerShell，跑下面这两行。第一行是提醒程序：这次检查你写的 lab，别误跑参考答案。

```powershell
$env:LEARN_TARGET = "lab"
uv run pytest tests/test_08_fastapi_sql.py -v
```

想只看一道题，就在命令后面加 `-k 关键词`，关键词可以从链接里的测试文件名和函数名里挑。要是看到 SKIPPED，那是这项没跑，不是做对了；先看看是不是少装了依赖。

## 做完了，试着给自己讲一遍

1. 先合上答案，说说每个函数或类吃进去什么、交回来什么，遇到什么会报错。
2. 挑一个边界例子，比如空输入或刚好卡在阈值上，自己走一遍每一步。
3. 挑一处语法讲给自己听：为什么这么写？换个写法还能不能做，区别在哪里？
4. 最后跑一下 lab 模式的测试。如果有列表、字典或状态，再看看原数据有没有被你不小心改掉。

## 接着往哪一节走

[项目说明](../../README.md) · [学习路线](../../ROADMAP.md) · [上一节](../07_internals/README.md) · [下一节](../09_cache_redis/README.md)
