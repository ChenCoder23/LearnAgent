"""第 1 章测试：容器、字符串、可变性。

跑法：uv run pytest tests/test_01_python_core.py
"""

from __future__ import annotations

import pytest

from learnkit import load

m = load("01_python_core")


def test_dedupe_keeps_first_seen_order():
    assert m.dedupe([3, 1, 3, 2, 1]) == [3, 1, 2]
    assert m.dedupe("banana") == ["b", "a", "n"]
    assert m.dedupe([]) == []


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "1.2.3",
            {"major": 1, "minor": 2, "patch": 3, "pre": None, "build": None},
        ),
        (
            "1.2.3-rc.1+b5",
            {"major": 1, "minor": 2, "patch": 3, "pre": "rc.1", "build": "b5"},
        ),
        (
            "01.00.010",
            {"major": 1, "minor": 0, "patch": 10, "pre": None, "build": None},
        ),
    ],
)
def test_parse_version_ok(text, expected):
    assert m.parse_version(text) == expected


@pytest.mark.parametrize("bad", ["1.2", "1.2.x", "", "1.2.3-", "1.2.3+", "a.b.c", "1.2.3.4"])
def test_parse_version_rejects_bad_input(bad):
    with pytest.raises(ValueError):
        m.parse_version(bad)


def test_group_by_supports_field_name_and_callable():
    rows = [
        {"t": "a", "v": 1},
        {"t": "b", "v": 2},
        {"t": "a", "v": 3},
    ]
    assert m.group_by(rows, "t") == {
        "a": [rows[0], rows[2]],
        "b": [rows[1]],
    }
    assert m.group_by([1, 2, 3, 4], lambda n: n % 2) == {1: [1, 3], 0: [2, 4]}
    assert m.group_by([], "t") == {}


def test_flatten_is_recursive_and_keeps_str_dict_as_leaf():
    assert m.flatten([1, [2, (3, None)], "ab"]) == [1, 2, 3, "ab"]
    assert m.flatten([None, [None, 1]], skip_none=False) == [None, None, 1]
    assert m.flatten([{"a": 1}, ["x"]]) == [{"a": 1}, "x"]


def test_chunk_boundaries():
    assert m.chunk([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]
    assert m.chunk([], 3) == []
    assert m.chunk([1, 2], 5) == [[1, 2]]
    with pytest.raises(ValueError):
        m.chunk([1], 0)


def test_deep_get_paths():
    data = {"a": {"b": [{"c": 7}, {"c": 8}]}, "n": None}
    assert m.deep_get(data, "a.b.0.c") == 7
    assert m.deep_get(data, "a.b.1.c") == 8
    assert m.deep_get(data, "a.b.9.c", default=-1) == -1
    assert m.deep_get(data, "a.x") is None
    assert m.deep_get(data, "n.deeper", default="fallback") == "fallback"
    assert m.deep_get(data, "") is None


def test_normalize_text():
    assert m.normalize("  hello\u3000 world\u200b ") == "hello world"
    assert m.normalize("a\t\tb\nc") == "a b c"
    assert m.normalize("") == ""


def test_summarize_stats():
    assert m.summarize([1, 3, 2, 4]) == {"min": 1, "max": 4, "mean": 2.5, "median": 2.5}
    assert m.summarize([5]) == {"min": 5, "max": 5, "mean": 5, "median": 5}
    assert m.summarize([4, 1, 3])["median"] == 3
    with pytest.raises(ValueError):
        m.summarize([])


def test_add_tag_never_shares_state():
    assert m.add_tag("a") == ["a"]
    assert m.add_tag("b", ["a"]) == ["a", "b"]
    source = ["x"]
    m.add_tag("y", source)
    assert source == ["x"], "不允许修改传入的 list"
    first = m.add_tag("p")
    second = m.add_tag("q")
    assert first == ["p"] and second == ["q"], "经典默认参数陷阱"


def test_merge_config_is_pure_and_recursive():
    base = {"db": {"host": "a", "port": 1}, "debug": False, "list": [1]}
    override = {"db": {"port": 2}, "list": [2, 3]}
    merged = m.merge_config(base, override)
    assert merged == {"db": {"host": "a", "port": 2}, "debug": False, "list": [2, 3]}
    assert base == {"db": {"host": "a", "port": 1}, "debug": False, "list": [1]}
    assert merged["list"] is not override["list"], "深拷贝，别把外部引用塞进来"
