"""阶段零 · 第 C 章测试：字符串、列表、字典。"""

from __future__ import annotations

import pytest

from learnkit import load

m = load("00c_data_basics")


def test_count_chars():
    assert m.count_chars("aba") == {"a": 2, "b": 1}
    assert m.count_chars("") == {}
    assert m.count_chars("aaa") == {"a": 3}


def test_word_count():
    assert m.word_count("a b a") == {"a": 2, "b": 1}
    assert m.word_count("  ") == {}
    assert m.word_count("hi") == {"hi": 1}


def test_reverse_words():
    assert m.reverse_words("hello world") == "world hello"
    assert m.reverse_words("a") == "a"
    assert m.reverse_words("") == ""


def test_capitalize_words():
    assert m.capitalize_words("hello world") == "Hello World"
    assert m.capitalize_words("python is fun") == "Python Is Fun"


def test_filter_even_returns_new_list():
    source = [1, 2, 3, 4]
    result = m.filter_even(source)
    assert result == [2, 4]
    assert source == [1, 2, 3, 4], "不要修改传入的列表"
    assert m.filter_even([]) == []


def test_list_stats():
    assert m.list_stats([1, 2, 3]) == {"min": 1, "max": 3, "sum": 6, "count": 3}
    assert m.list_stats([5]) == {"min": 5, "max": 5, "sum": 5, "count": 1}
    with pytest.raises(ValueError):
        m.list_stats([])


def test_pairs_to_dict():
    assert m.pairs_to_dict([("a", 1), ("b", 2)]) == {"a": 1, "b": 2}
    assert m.pairs_to_dict([]) == {}
    assert m.pairs_to_dict([("a", 1), ("a", 9)]) == {"a": 9}


def test_get_or_default():
    data = {"a": 1}
    assert m.get_or_default(data, "a", 0) == 1
    assert m.get_or_default(data, "b", 0) == 0
    assert data == {"a": 1}, "不要往字典里塞默认值"


def test_remove_duplicates_keeps_order():
    assert m.remove_duplicates([1, 2, 1, 3, 2]) == [1, 2, 3]
    assert m.remove_duplicates([]) == []
    source = [1, 1]
    m.remove_duplicates(source)
    assert source == [1, 1], "不要修改传入的列表"


def test_join_names():
    assert m.join_names(["a", "b"]) == "a, b"
    assert m.join_names(["a", "b"], "-") == "a-b"
    assert m.join_names([]) == ""


def test_find_max_key():
    assert m.find_max_key({"a": 1, "b": 3}) == "b"
    assert m.find_max_key({"a": 5}) == "a"
    assert m.find_max_key({}) is None
    assert m.find_max_key({"a": -1, "b": -5}) == "a"
