# 02 · 闭包、装饰器与函数组合：语法与设计思路

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

## 原理明白了，再看看这章会怎样用到它们

### 闭包与绑定时机

make_counter 的内层函数捕获外层 current；重新赋值需要 nonlocal。循环里 lambda: i 捕获的是变量，调用时才取值；默认参数、工厂或 partial 可以固定每次的值。

### 装饰器的层次

retry 同时支持 @retry 和 @retry(times=3)：外层解析选项，decorator 接收目标函数，wrapper 执行调用。wraps 保留名称、文档等元数据。

### 重试与计时

times 是总尝试次数；只捕获指定异常，最后一次直接 raise。timed 使用 perf_counter，finally 保证失败也记录耗时。

### 缓存与哨兵

memoize 用实参和排序后的关键字参数构造键，并先检查是否可哈希；不可哈希时直接计算。once 使用独立 object() 区分未执行和执行结果为 None。

### 分派与签名

singledispatch 按首参数运行时类型及继承关系查实现。inspect.signature 用于筛选可接受的关键字参数；该教学适配器不是完整的 Python 参数绑定器。

## 顺着这章，还能多理解一点什么

重试可能重复副作用，生产使用时要结合幂等性。缓存键还可以做签名归一化，让 f(1) 与 f(a=1) 等价；本题的参考键没有完成这种归一化。

## 先看一小段代码，把语法拆开聊

```python
from functools import wraps

def record_name(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper
```

*args 收集位置参数为元组，**kwargs 收集关键字参数为字典；调用时的 * 与 ** 则把它们展开。@decorator 等价于把函数替换成 decorator(func)。

顺便认一下题目里常见的注解：`list[str]` 是“里面放字符串的列表”，`str | None` 是“字符串或者空值”，`->` 后面写返回什么类型。它们主要是在说明接口，不会替你检查或转换输入。`from __future__ import annotations` 则让注解暂时不求值，第 16 章会用到这个细节。

## 卡住了，先看看这些地方

- compose(f, g) 从右往左执行，pipeline_timer 按列表顺序执行。
- 结果为 None 也可能是缓存命中，不要用 truthiness 判断。
- bool 是 int 的子类，会影响单分派选择。

报错时，先去看失败测试里的 assert 或 pytest.raises：它到底希望得到什么？再回头检查类型、边界和返回值。NotImplementedError 通常是还有一处没写完，ImportError 则先去查环境和依赖。

想确认是不是自己的实现出了问题，可以暂时跑一下参考答案。下面用 finally 把模式切回 lab，省得下次不小心检查了答案，却以为自己做完了。

```powershell
$env:LEARN_TARGET = "solutions"
try {
    uv run pytest tests/test_02_functions.py -v
} finally {
    $env:LEARN_TARGET = "lab"
}
```

## 先打开哪些文件，怎么跑起来

- [练习文件](lab.py)：填写实现，保留函数名与签名。
- [参考实现](solutions.py)：卡住后对照，理解后合上重写。
- [验收测试](../../tests/test_02_functions.py)：核对准确输出、错误路径和边界。

打开仓库根目录下的 PowerShell，跑下面这两行。第一行是提醒程序：这次检查你写的 lab，别误跑参考答案。

```powershell
$env:LEARN_TARGET = "lab"
uv run pytest tests/test_02_functions.py -v
```

想只看一道题，就在命令后面加 `-k 关键词`，关键词可以从链接里的测试文件名和函数名里挑。要是看到 SKIPPED，那是这项没跑，不是做对了；先看看是不是少装了依赖。

## 做完了，试着给自己讲一遍

1. 先合上答案，说说每个函数或类吃进去什么、交回来什么，遇到什么会报错。
2. 挑一个边界例子，比如空输入或刚好卡在阈值上，自己走一遍每一步。
3. 挑一处语法讲给自己听：为什么这么写？换个写法还能不能做，区别在哪里？
4. 最后跑一下 lab 模式的测试。如果有列表、字典或状态，再看看原数据有没有被你不小心改掉。

## 接着往哪一节走

[项目说明](../../README.md) · [学习路线](../../ROADMAP.md) · [上一节](../01_python_core/README.md) · [下一节](../03_oop/README.md)
