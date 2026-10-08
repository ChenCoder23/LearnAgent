# 12 · 文档切分、向量检索与 RAG：语法与设计思路

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

### 文档与来源

Document.page_content 保存正文，metadata 保存 source、chunk_id 等来源信息。切分后元数据必须保留，否则答案无法回溯资料。

### 切分与重叠

RecursiveCharacterTextSplitter 根据分隔符分层切块，overlap 保留相邻上下文。过大的块降低定位精度，过小的块丢失语境；这里 chunk_id 按输出全局递增。

### 哈希向量

HashEmbeddings 将英文词和字符 bigram 映射到固定维度，统计频次后做 L2 归一化。md5 摘要保证跨进程稳定，不用于安全加密；空向量需避免除零。

### 向量库与检索器

InMemoryVectorStore 写入文档并计算向量；similarity_search 返回相似片段，as_retriever 把查询适配为可执行组件，k 控制最多取多少结果。

### 问答与去重

dedupe_documents 按正文保序去重，format_docs 给片段加来源标记。answer_question 的提示要求只根据资料、资料不足说不知道，但提示本身不能保证模型绝不编造。

## 顺着这章，还能多理解一点什么

哈希词袋反映字面重合，不等于语义 embedding；同义句、中文分词和哈希碰撞都会影响结果。生产还需检索评估、来源核对、阈值与权限过滤。

## 先看一小段代码，把语法拆开聊

```python
import hashlib

token = "python"
digest = hashlib.md5(token.encode("utf-8")).hexdigest()
index = int(digest, 16) % 64
assert 0 <= index < 64
```

encode 将字符串编码为字节，hexdigest 得到十六进制文本，int(..., 16) 转整数，% 把值映射到向量维度。

顺便认一下题目里常见的注解：`list[str]` 是“里面放字符串的列表”，`str | None` 是“字符串或者空值”，`->` 后面写返回什么类型。它们主要是在说明接口，不会替你检查或转换输入。`from __future__ import annotations` 则让注解暂时不求值，第 16 章会用到这个细节。

## 卡住了，先看看这些地方

- 文档未切分就大块入库，会影响上下文长度和命中精度。
- 先测试 retrieve 的命中，再排查模型回答。
- 当前实现用内存向量库，测试无需部署独立向量数据库。

报错时，先去看失败测试里的 assert 或 pytest.raises：它到底希望得到什么？再回头检查类型、边界和返回值。NotImplementedError 通常是还有一处没写完，ImportError 则先去查环境和依赖。

想确认是不是自己的实现出了问题，可以暂时跑一下参考答案。下面用 finally 把模式切回 lab，省得下次不小心检查了答案，却以为自己做完了。

```powershell
$env:LEARN_TARGET = "solutions"
try {
    uv run pytest tests/test_12_rag.py -v
} finally {
    $env:LEARN_TARGET = "lab"
}
```

## 先打开哪些文件，怎么跑起来

- [练习文件](lab.py)：填写实现，保留函数名与签名。
- [参考实现](solutions.py)：卡住后对照，理解后合上重写。
- [验收测试](../../tests/test_12_rag.py)：核对准确输出、错误路径和边界。

打开仓库根目录下的 PowerShell，跑下面这两行。第一行是提醒程序：这次检查你写的 lab，别误跑参考答案。

```powershell
$env:LEARN_TARGET = "lab"
uv run pytest tests/test_12_rag.py -v
```

想只看一道题，就在命令后面加 `-k 关键词`，关键词可以从链接里的测试文件名和函数名里挑。要是看到 SKIPPED，那是这项没跑，不是做对了；先看看是不是少装了依赖。

## 做完了，试着给自己讲一遍

1. 先合上答案，说说每个函数或类吃进去什么、交回来什么，遇到什么会报错。
2. 挑一个边界例子，比如空输入或刚好卡在阈值上，自己走一遍每一步。
3. 挑一处语法讲给自己听：为什么这么写？换个写法还能不能做，区别在哪里？
4. 最后跑一下 lab 模式的测试。如果有列表、字典或状态，再看看原数据有没有被你不小心改掉。

## 接着往哪一节走

[项目说明](../../README.md) · [学习路线](../../ROADMAP.md) · [上一节](../11_lcel_runnable/README.md) · [下一节](../13_agent_tools/README.md)
