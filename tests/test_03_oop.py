"""第 3 章测试：值对象、魔术方法、MRO、描述符、抽象基类。"""

from __future__ import annotations

from decimal import Decimal

import pytest

from learnkit import load

m = load("03_oop")


def test_vector_value_semantics():
    v = m.Vector(1, 2)
    w = m.Vector(3, 4)
    assert v + w == m.Vector(4, 6)
    assert w - v == m.Vector(2, 2)
    assert v * 3 == m.Vector(3, 6)
    assert 3 * v == m.Vector(3, 6)
    assert v != w
    assert v == m.Vector(1, 2)
    assert repr(v) == "Vector(1, 2)"
    assert abs(m.Vector(3, 4)) == pytest.approx(5.0)
    assert len({m.Vector(1, 2), m.Vector(1, 2), m.Vector(3, 4)}) == 2


def test_money_is_immutable_and_ordered():
    a = m.Money(Decimal("10.00"))
    b = m.Money(Decimal("2.50"))
    assert a + b == m.Money(Decimal("12.50"))
    assert b < a
    assert a > b
    assert sorted([a, b]) == [b, a]
    with pytest.raises(Exception):
        a.amount = Decimal("1")  # frozen dataclass 不允许赋值
    with pytest.raises(m.CurrencyMismatchError):
        a + m.Money(Decimal("1"), "USD")


def test_article_repo_cooperative_init_and_mro():
    repo = m.ArticleRepo()
    assert repo.trace == ["TraceMixin", "CacheMixin", "BaseRepo", "ArticleRepo"]
    assert repo.name == "articles"
    assert repo.build_cache_key("42") == "articles:42"
    assert [cls.__name__ for cls in m.ArticleRepo.__mro__][:4] == [
        "ArticleRepo",
        "TraceMixin",
        "CacheMixin",
        "BaseRepo",
    ]


def test_positive_descriptor_validates():
    product = m.Product("键盘", 199)
    assert product.price == 199
    product.price = 50.5
    assert product.price == 50.5
    with pytest.raises(ValueError):
        product.price = 0
    with pytest.raises(ValueError):
        product.price = -1
    with pytest.raises(ValueError):
        m.Product("鼠标", "贵")
    assert isinstance(m.Product.price, m.Positive), "类属性上应该是描述符本身"


def test_abstract_base_class_enforced():
    with pytest.raises(TypeError):
        m.Shape()
    circle = m.Circle(2)
    rect = m.Rect(2, 3)
    assert circle.area() == pytest.approx(12.566, rel=1e-3)
    assert rect.area() == 6
    assert m.total_area([circle, rect]) == pytest.approx(18.566, rel=1e-3)
    assert rect.describe() == "Rect(area=6.00)"
    assert isinstance(rect, m.Shape)


def test_user_properties_validate_and_repr():
    user = m.User("  Ann ", "a@b.c")
    assert user.name == "Ann"
    assert repr(user) == "User(name='Ann', email='a@b.c')"
    user.name = "Bob"
    assert user.name == "Bob"
    with pytest.raises(ValueError):
        m.User("   ", "a@b.c")
    with pytest.raises(ValueError):
        user.email = "not-an-email"


def test_slots_save_memory():
    plain, slots = m.instance_sizes()
    assert slots < plain
    assert not hasattr(m.SlotsPoint(1, 2), "__dict__")
    assert hasattr(m.DictPoint(1, 2), "__dict__")


def test_callable_object():
    assert m.Multiplier(3)(4) == 12
    assert callable(m.Multiplier(2))
