# 03 · 值对象、继承、描述符与多态：语法与设计思路

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

### 运算协议与哈希

__add__ 等方法让对象参与运算；__rmul__ 处理 2 * v。相等对象得有相同哈希，参与哈希的字段应保持稳定；NotImplemented 是返回给运算协议的特殊值，不同于抛 NotImplementedError。

### 金额与数据类

Money 用 Decimal 保存金额，用 frozen=True 数据类避免正常属性赋值，并检查币种后才计算。total_ordering 根据已有的比较方法补齐排序运算。

### 协作继承

super() 沿 MRO 继续调用，不一定是文本上写出的某个父类。Mixin 使用 *args/**kwargs 转发参数，trace 的追加位置决定记录的是进入还是退出顺序。

### 描述符与属性

Positive.__set_name__ 记录属性名，__get__/__set__ 控制实例读写。property/setter 把 name 的清洗校验集中在属性入口；类访问描述符时要处理 instance is None。

### 抽象与多态

ABC 和 abstractmethod 声明接口，Circle/Rect 实现 area，total_area 只调用协议方法。__slots__ 限制实例属性，__call__ 让 Multiplier 实例像函数一样被调用。

## 顺着这章，还能多理解一点什么

不可变值对象适合做字典键，但 __slots__ 本身不会让字段只读。本仓库 Vector 的题面要求只读，而参考实现的 x/y 可以赋值；实现时应理解并维护哈希字段稳定性，不能把参考代码视作完整不可变设计。

## 先看一小段代码，把语法拆开聊

```python
from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class Amount:
    value: Decimal

assert Amount(Decimal("0.1")) == Amount(Decimal("0.1"))
```

class 定义类型，self 指向实例，装饰器可修改类的构建行为。Decimal 从字符串创建，避免先产生 float 的近似误差。

顺便认一下题目里常见的注解：`list[str]` 是“里面放字符串的列表”，`str | None` 是“字符串或者空值”，`->` 后面写返回什么类型。它们主要是在说明接口，不会替你检查或转换输入。`from __future__ import annotations` 则让注解暂时不求值，第 16 章会用到这个细节。

## 卡住了，先看看这些地方

- super 链漏掉一环会让 name 或 trace 未初始化。
- sys.getsizeof 只反映被测对象直接占用，普通实例的字典需要另外考虑。
- 不要把返回 NotImplemented 写成 raise NotImplemented。

报错时，先去看失败测试里的 assert 或 pytest.raises：它到底希望得到什么？再回头检查类型、边界和返回值。NotImplementedError 通常是还有一处没写完，ImportError 则先去查环境和依赖。

想确认是不是自己的实现出了问题，可以暂时跑一下参考答案。下面用 finally 把模式切回 lab，省得下次不小心检查了答案，却以为自己做完了。

```powershell
$env:LEARN_TARGET = "solutions"
try {
    uv run pytest tests/test_03_oop.py -v
} finally {
    $env:LEARN_TARGET = "lab"
}
```

## 先打开哪些文件，怎么跑起来

- [练习文件](lab.py)：填写实现，保留函数名与签名。
- [参考实现](solutions.py)：卡住后对照，理解后合上重写。
- [验收测试](../../tests/test_03_oop.py)：核对准确输出、错误路径和边界。

打开仓库根目录下的 PowerShell，跑下面这两行。第一行是提醒程序：这次检查你写的 lab，别误跑参考答案。

```powershell
$env:LEARN_TARGET = "lab"
uv run pytest tests/test_03_oop.py -v
```

想只看一道题，就在命令后面加 `-k 关键词`，关键词可以从链接里的测试文件名和函数名里挑。要是看到 SKIPPED，那是这项没跑，不是做对了；先看看是不是少装了依赖。

## 做完了，试着给自己讲一遍

1. 先合上答案，说说每个函数或类吃进去什么、交回来什么，遇到什么会报错。
2. 挑一个边界例子，比如空输入或刚好卡在阈值上，自己走一遍每一步。
3. 挑一处语法讲给自己听：为什么这么写？换个写法还能不能做，区别在哪里？
4. 最后跑一下 lab 模式的测试。如果有列表、字典或状态，再看看原数据有没有被你不小心改掉。

## 接着往哪一节走

[项目说明](../../README.md) · [学习路线](../../ROADMAP.md) · [上一节](../02_functions/README.md) · [下一节](../04_iter_gen_exc/README.md)
