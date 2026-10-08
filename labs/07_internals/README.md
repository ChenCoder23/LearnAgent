# 07 · 对象身份、垃圾回收与运行原理：语法与设计思路

这一节，咱们先从“变量不是盒子，先理解“名字指向对象””聊起。先理解 Python 的规则和设计思路，再看它们能怎么用。你可以边读边运行小例子，别急着背结论。

咱们先把语言本身讲明白：语法怎么写、代码为什么这样工作、设计上有什么取舍。后面再把这些原理和本节实验联系起来，不按题目挨个拆答案。

## 先聊 Python 的语法和设计思路

这一部分先不看题。咱们从语言规则讲起，用小例子看看它为什么这样工作，再聊这种设计带来的方便和需要留意的地方。后面回到 lab，你就能把代码和这些原理对上。

### 变量不是盒子，先理解“名字指向对象”

你可能习惯把变量想成一个装值的盒子。学 Python 时，换成“名字贴在对象上”会更好理解。比如 `a = [1]`，右边先创建一个列表对象，左边的 a 只是绑定到它的名字。接着写 `b = a`，没有再造一个列表，两个名字指向的是同一份东西。

所以你通过 b 追加元素，a 也能看见；但如果写 `b = [9]`，只是让 b 改为指向一个新列表，a 还指着旧列表。这就是“修改对象”和“重新绑定名字”的区别。Python 用这一套模型处理函数传参、容器元素和对象属性，先弄清它，后面很多坑就不用硬背了。

类型跟着对象走，不是永远写死在变量名上。a 现在指向列表，下一行也可以指向字符串。不过能这么写，不代表业务里频繁换类型好读。给名字一个稳定含义，代码通常更容易理解。

```python
a = [1]
b = a
b.append(2)
assert a == [1, 2]
b = [9]
assert a == [1, 2]
```

这里 `a is b` 问的是两者现在是否指向同一个对象，`a == b` 问的是值是否相等。比较空值常用 `is None`；比较业务里的字符串和数字，一般用 `==`。

### 语言保证和解释器实验，要分开理解

名字绑定、迭代协议这些是 Python 语义；小整数缓存、引用计数、字节码细节则常和解释器实现有关。你可以用实验理解当前 CPython 的行为，但别把一次观察当成所有版本都必须这样。

比如 == 是值比较，is 是身份比较。字面量可能被编译器复用，运行时拼接的同值字符串也可能是不同对象，业务判断不该赌驻留优化。sys.getrefcount 的调用自身还会临时增加引用，所以更适合看前后差值。

```python
a = [1]
b = [1]
assert a == b
assert a is not b
```

del 删除一个绑定，其他强引用还在，对象就仍能活着。循环引用需要垃圾回收机制处理，弱引用不会替对象延长生命。dis 帮你看编译后的指令，但 Python 版本变化时指令也会变；timeit 帮你测量，不过得控制输入、次数和副作用，才能比较得有意义。

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

### 属性访问也有协议：校验可以放在统一入口

`obj.price` 看着只是读一个字段，背后也能经过方法。property 用方法提供属性接口，描述符则把这套读写规则做成可复用对象。你可以把校验放在入口，让初始化和之后赋值遵守同样的规则。

```python
class Temperature:
    def __init__(self, value):
        self.value = value
    @property
    def value(self):
        return self._value
    @value.setter
    def value(self, value):
        if value < -273.15:
            raise ValueError("低于绝对零度")
        self._value = value
```

描述符通过 __get__、__set__ 介入访问，__set_name__ 能在类创建时知道自己被放在哪个属性名下。类访问时 instance 可能是 None，要和实例访问分开处理。

常规查找没找到属性时，__getattr__ 才有机会补救，所以它适合懒加载。__getattribute__ 则覆盖更广，改写它时容易连内部访问也递归进去；需要时用 object 的实现绕开自定义逻辑。属性魔法方便，但也会隐藏实际开销，耗时的操作最好让调用者知道。

## 原理明白了，再看看这章会怎样用到它们

### 身份与相等

== 比较值，is 比较是否同一对象。小整数缓存与字符串驻留能解释某些身份相同，但缓存范围和优化行为不是所有 Python 实现的保证。

### 引用与回收

sys.getrefcount 调用本身会暂时增加引用。容器保存对象时多一个强引用；循环引用需结合 gc 观察，del 删除的是名称绑定，不是强制销毁对象。

### 字节码

dis.get_instructions 把函数编译后的指令逐项列出。嵌套函数与推导式可能包含独立 code 对象，recursive=True 时继续检查它们；指令名称依赖 Python 版本。

### 属性查找

__getattr__ 只在常规属性查找失败后调用，LazyConfig 在这里加载并缓存。实现内部用 object.__getattribute__/__setattr__ 访问底层属性，避免误入自定义查找逻辑。

### 拷贝与弱引用

copy.copy 复制外层，deepcopy 复制嵌套图。WeakValueDictionary 不延长值的生命周期，最后一个强引用消失后项可被回收。timeit 返回多次执行的总耗时。

## 顺着这章，还能多理解一点什么

第 01 章的默认参数陷阱在这里从函数对象角度再验证。优化先测量，再分析复杂度和分配成本；不要把单次运行或某个字节码名字当跨版本结论。

## 先看一小段代码，把语法拆开聊

```python
import copy

original = [[1]]
shallow = copy.copy(original)
deep = copy.deepcopy(original)
shallow[0].append(2)
assert original == [[1, 2]]
assert deep == [[1]]
```

shallow is original，初值用 False，但 shallow[0] is original[0]，初值用 True。对象身份与内容相等是两个独立问题。

顺便认一下题目里常见的注解：`list[str]` 是“里面放字符串的列表”，`str | None` 是“字符串或者空值”，`->` 后面写返回什么类型。它们主要是在说明接口，不会替你检查或转换输入。`from __future__ import annotations` 则让注解暂时不求值，第 16 章会用到这个细节。

## 卡住了，先看看这些地方

- getrefcount 关注前后差值，不要硬编码绝对引用数。
- 不要用 is 比较普通字符串或数值业务结果。
- weak_cache_roundtrip 中强引用必须释放，才有可能观察到缓存缩小。

报错时，先去看失败测试里的 assert 或 pytest.raises：它到底希望得到什么？再回头检查类型、边界和返回值。NotImplementedError 通常是还有一处没写完，ImportError 则先去查环境和依赖。

想确认是不是自己的实现出了问题，可以暂时跑一下参考答案。下面用 finally 把模式切回 lab，省得下次不小心检查了答案，却以为自己做完了。

```powershell
$env:LEARN_TARGET = "solutions"
try {
    uv run pytest tests/test_07_internals.py -v
} finally {
    $env:LEARN_TARGET = "lab"
}
```

## 先打开哪些文件，怎么跑起来

- [练习文件](lab.py)：填写实现，保留函数名与签名。
- [参考实现](solutions.py)：卡住后对照，理解后合上重写。
- [验收测试](../../tests/test_07_internals.py)：核对准确输出、错误路径和边界。

打开仓库根目录下的 PowerShell，跑下面这两行。第一行是提醒程序：这次检查你写的 lab，别误跑参考答案。

```powershell
$env:LEARN_TARGET = "lab"
uv run pytest tests/test_07_internals.py -v
```

想只看一道题，就在命令后面加 `-k 关键词`，关键词可以从链接里的测试文件名和函数名里挑。要是看到 SKIPPED，那是这项没跑，不是做对了；先看看是不是少装了依赖。

## 做完了，试着给自己讲一遍

1. 先合上答案，说说每个函数或类吃进去什么、交回来什么，遇到什么会报错。
2. 挑一个边界例子，比如空输入或刚好卡在阈值上，自己走一遍每一步。
3. 挑一处语法讲给自己听：为什么这么写？换个写法还能不能做，区别在哪里？
4. 最后跑一下 lab 模式的测试。如果有列表、字典或状态，再看看原数据有没有被你不小心改掉。

## 接着往哪一节走

[项目说明](../../README.md) · [学习路线](../../ROADMAP.md) · [上一节](../06_concurrency_async/README.md) · [下一节](../08_fastapi_sql/README.md)
