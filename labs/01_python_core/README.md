# 01 · 容器、可变性与数据转换：语法与设计思路

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

## 原理明白了，再看看这章会怎样用到它们

### 哈希与保序

dedupe 用 set 记录见过的元素，用 list 记录输出顺序。set 提供平均 O(1) 的成员判断，但输出仍需依赖列表；列表和字典本身不能作为 set 元素。

### 解析与导航

parse_version 分离 +build、-pre 和三段数字，属于本题的简化版本格式，不是完整 SemVer 验证器。deep_get 每走一段都检查当前是字典还是序列，缺失、越界或类型不符返回 default。

### 高阶函数与分组

group_by 接受字段名或函数。callable 判定函数形式，lambda 把字段名适配成取值函数，defaultdict(list) 为每个新分组生成独立列表。

### 栈、切片与统计

flatten 用显式栈展开 list/tuple；为保持左到右顺序，入栈时反转子项。chunk 用 seq[i:i+size] 切片；中位数先排序，奇数取中间，偶数取两项平均。

### 拷贝与默认参数

默认参数在函数定义时创建。add_tag 用 None 哨兵，每次创建新列表；merge_config 递归合并嵌套字典，并深拷贝被保留或替换的值，避免共享可变子对象。

## 顺着这章，还能多理解一点什么

文本归一化会影响搜索与缓存键：split/join 能压缩空白，零宽字符需要显式清除。浅拷贝只复制外层容器，深拷贝复制嵌套对象，第 07 章会通过实验验证。

## 先看一小段代码，把语法拆开聊

```python
def append_copy(value, items=None):
    result = list(items) if items is not None else []
    result.append(value)
    return result

source = [1]
assert append_copy(2, source) == [1, 2]
assert source == [1]
```

条件表达式 a if condition else b 根据条件产生一个值；is not None 检查空值身份。list(items) 创建新的外层列表，不会深拷贝其中的对象。

顺便认一下题目里常见的注解：`list[str]` 是“里面放字符串的列表”，`str | None` 是“字符串或者空值”，`->` 后面写返回什么类型。它们主要是在说明接口，不会替你检查或转换输入。`from __future__ import annotations` 则让注解暂时不求值，第 16 章会用到这个细节。

## 卡住了，先看看这些地方

- flatten 把字符串和字典当叶子，不要把它们拆开。
- chunk 的 size <= 0 必须先报错。
- 合并后再修改嵌套值，原配置也不应受到影响。

报错时，先去看失败测试里的 assert 或 pytest.raises：它到底希望得到什么？再回头检查类型、边界和返回值。NotImplementedError 通常是还有一处没写完，ImportError 则先去查环境和依赖。

想确认是不是自己的实现出了问题，可以暂时跑一下参考答案。下面用 finally 把模式切回 lab，省得下次不小心检查了答案，却以为自己做完了。

```powershell
$env:LEARN_TARGET = "solutions"
try {
    uv run pytest tests/test_01_python_core.py -v
} finally {
    $env:LEARN_TARGET = "lab"
}
```

## 先打开哪些文件，怎么跑起来

- [练习文件](lab.py)：填写实现，保留函数名与签名。
- [参考实现](solutions.py)：卡住后对照，理解后合上重写。
- [验收测试](../../tests/test_01_python_core.py)：核对准确输出、错误路径和边界。

打开仓库根目录下的 PowerShell，跑下面这两行。第一行是提醒程序：这次检查你写的 lab，别误跑参考答案。

```powershell
$env:LEARN_TARGET = "lab"
uv run pytest tests/test_01_python_core.py -v
```

想只看一道题，就在命令后面加 `-k 关键词`，关键词可以从链接里的测试文件名和函数名里挑。要是看到 SKIPPED，那是这项没跑，不是做对了；先看看是不是少装了依赖。

## 做完了，试着给自己讲一遍

1. 先合上答案，说说每个函数或类吃进去什么、交回来什么，遇到什么会报错。
2. 挑一个边界例子，比如空输入或刚好卡在阈值上，自己走一遍每一步。
3. 挑一处语法讲给自己听：为什么这么写？换个写法还能不能做，区别在哪里？
4. 最后跑一下 lab 模式的测试。如果有列表、字典或状态，再看看原数据有没有被你不小心改掉。

## 接着往哪一节走

[项目说明](../../README.md) · [学习路线](../../ROADMAP.md) · [上一节](../00c_data_basics/README.md) · [下一节](../02_functions/README.md)
