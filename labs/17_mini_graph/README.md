# 17 · 手写状态图、路由与检查点：语法与设计思路

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

### 状态合并

普通字段覆盖，messages 在两边都是列表时追加。创建新的外层状态和消息列表，避免修改调用者输入；这只是简化 reducer，不包含真实 add_messages 的消息 ID 处理。

### 图定义与编译

StateGraph 保存节点函数、固定边、条件边和入口；add_* 返回 self 支持链式构建。compile 复制定义并生成 CompiledGraph，缺入口必须报错。

### 条件路由

router 根据合并后的状态返回标记，mapping 将标记翻译为节点名；没有 mapping 时返回值直接作为节点名。找不到目标或映射必须暴露错误。

### 执行与上限

从入口开始 while current != END，执行节点、合并更新、选择下一节点；history 记录访问顺序。recursion_limit 是节点执行步数上限，不是 Python 调用栈深度。

### 会话记忆

config.configurable.thread_id 指定会话。开始时读取快照并合并新输入，正常结束写回；MemoryCheckpointer 的 put/get 都深拷贝，隔离调用者与存档对象。

## 顺着这章，还能多理解一点什么

题面 next_node 写固定边优先，参考实现是条件边优先，当前测试没有覆盖两种边共存。做练习时不要给同一节点同时配置两种边；若扩展，应先明确优先级并补测试。

## 先看一小段代码，把语法拆开聊

```python
state = {"count": 1, "messages": ["hello"]}
update = {"count": 2, "messages": ["reply"]}
merged = {**state, **update}
merged["messages"] = [*state["messages"], *update["messages"]]
assert merged == {"count": 2, "messages": ["hello", "reply"]}
assert state["messages"] == ["hello"]
```

** 展开字典，后面的同名键覆盖前面的键；* 展开列表元素。新列表连接消息，避免对原 state 的消息列表原地 append。

顺便认一下题目里常见的注解：`list[str]` 是“里面放字符串的列表”，`str | None` 是“字符串或者空值”，`->` 后面写返回什么类型。它们主要是在说明接口，不会替你检查或转换输入。`from __future__ import annotations` 则让注解暂时不求值，第 16 章会用到这个细节。

## 卡住了，先看看这些地方

- 节点返回 None 表示没有局部更新，不表示结束；是否结束由边决定。
- 同 thread_id 累积记忆，不同 thread_id 隔离。
- 当前检查点只在正常完成后保存，不支持中断后的逐节点恢复。

报错时，先去看失败测试里的 assert 或 pytest.raises：它到底希望得到什么？再回头检查类型、边界和返回值。NotImplementedError 通常是还有一处没写完，ImportError 则先去查环境和依赖。

想确认是不是自己的实现出了问题，可以暂时跑一下参考答案。下面用 finally 把模式切回 lab，省得下次不小心检查了答案，却以为自己做完了。

```powershell
$env:LEARN_TARGET = "solutions"
try {
    uv run pytest tests/test_17_mini_graph.py -v
} finally {
    $env:LEARN_TARGET = "lab"
}
```

## 先打开哪些文件，怎么跑起来

- [练习文件](lab.py)：填写实现，保留函数名与签名。
- [参考实现](solutions.py)：卡住后对照，理解后合上重写。
- [验收测试](../../tests/test_17_mini_graph.py)：核对准确输出、错误路径和边界。

打开仓库根目录下的 PowerShell，跑下面这两行。第一行是提醒程序：这次检查你写的 lab，别误跑参考答案。

```powershell
$env:LEARN_TARGET = "lab"
uv run pytest tests/test_17_mini_graph.py -v
```

想只看一道题，就在命令后面加 `-k 关键词`，关键词可以从链接里的测试文件名和函数名里挑。要是看到 SKIPPED，那是这项没跑，不是做对了；先看看是不是少装了依赖。

## 做完了，试着给自己讲一遍

1. 先合上答案，说说每个函数或类吃进去什么、交回来什么，遇到什么会报错。
2. 挑一个边界例子，比如空输入或刚好卡在阈值上，自己走一遍每一步。
3. 挑一处语法讲给自己听：为什么这么写？换个写法还能不能做，区别在哪里？
4. 最后跑一下 lab 模式的测试。如果有列表、字典或状态，再看看原数据有没有被你不小心改掉。

## 接着往哪一节走

[项目说明](../../README.md) · [学习路线](../../ROADMAP.md) · [上一节](../16_mini_agent/README.md)
