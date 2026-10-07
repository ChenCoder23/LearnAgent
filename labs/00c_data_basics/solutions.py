"""阶段零 · 第 C 章参考实现。"""

from __future__ import annotations


def count_chars(text: str) -> dict[str, int]:
    result: dict[str, int] = {}
    for char in text:
        result[char] = result.get(char, 0) + 1
    return result


def word_count(sentence: str) -> dict[str, int]:
    result: dict[str, int] = {}
    for word in sentence.split():
        result[word] = result.get(word, 0) + 1
    return result


def reverse_words(sentence: str) -> str:
    return " ".join(reversed(sentence.split()))


def capitalize_words(sentence: str) -> str:
    return " ".join(word.capitalize() for word in sentence.split())


def filter_even(numbers: list[int]) -> list[int]:
    result: list[int] = []
    for number in numbers:
        if number % 2 == 0:
            result.append(number)
    return result


def list_stats(numbers: list[float]) -> dict[str, float]:
    if not numbers:
        raise ValueError("列表不能为空")
    return {
        "min": min(numbers),
        "max": max(numbers),
        "sum": sum(numbers),
        "count": len(numbers),
    }


def pairs_to_dict(pairs: list[tuple[str, int]]) -> dict[str, int]:
    result: dict[str, int] = {}
    for key, value in pairs:
        result[key] = value
    return result


def get_or_default(data: dict[str, int], key: str, default: int) -> int:
    return data.get(key, default)


def remove_duplicates(items: list[int]) -> list[int]:
    result: list[int] = []
    for item in items:
        if item not in result:
            result.append(item)
    return result


def join_names(names: list[str], sep: str = ", ") -> str:
    return sep.join(names)


def find_max_key(data: dict[str, int]) -> str | None:
    best_key: str | None = None
    best_value: int | None = None
    for key, value in data.items():
        if best_value is None or value > best_value:
            best_key = key
            best_value = value
    return best_key
