"""阶段零 · 第 B 章参考实现。"""

from __future__ import annotations


def max_of_three(a: float, b: float, c: float) -> float:
    largest = a
    if b > largest:
        largest = b
    if c > largest:
        largest = c
    return largest


def grade(score: int) -> str:
    if score < 0 or score > 100:
        raise ValueError("分数必须在 0-100 之间")
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "E"


def sum_to(n: int) -> int:
    total = 0
    for number in range(1, n + 1):
        total += number
    return total


def count_vowels(text: str) -> int:
    count = 0
    for char in text.lower():
        if char in "aeiou":
            count += 1
    return count


def fizzbuzz(n: int) -> list[str]:
    result: list[str] = []
    for number in range(1, n + 1):
        if number % 15 == 0:
            result.append("FizzBuzz")
        elif number % 3 == 0:
            result.append("Fizz")
        elif number % 5 == 0:
            result.append("Buzz")
        else:
            result.append(str(number))
    return result


def find_first_even(numbers: list[int]) -> int:
    for index, value in enumerate(numbers):
        if value % 2 == 0:
            return index
    return -1


def multiplication_row(n: int) -> list[str]:
    result: list[str] = []
    for factor in range(1, n + 1):
        result.append(f"{factor}x{n}={factor * n}")
    return result


def is_prime(n: int) -> bool:
    if n < 2:
        return False
    divisor = 2
    while divisor * divisor <= n:
        if n % divisor == 0:
            return False
        divisor += 1
    return True


def countdown_while(n: int) -> list[int]:
    result: list[int] = []
    while n > 0:
        result.append(n)
        n -= 1
    return result


def sum_until_over(limit: int) -> tuple[int, int]:
    total = 0
    number = 0
    while total <= limit:
        number += 1
        total += number
    return total, number
