"""阶段零 · 第 B 章测试：判断与循环。"""

from __future__ import annotations

import pytest

from learnkit import load

m = load("00b_control_flow")


def test_max_of_three_all_positions():
    assert m.max_of_three(1, 2, 3) == 3
    assert m.max_of_three(3, 2, 1) == 3
    assert m.max_of_three(2, 3, 1) == 3
    assert m.max_of_three(5, 5, 1) == 5
    assert m.max_of_three(-1, -2, -3) == -1


def test_grade_boundaries():
    assert m.grade(100) == "A"
    assert m.grade(90) == "A"
    assert m.grade(89) == "B"
    assert m.grade(80) == "B"
    assert m.grade(70) == "C"
    assert m.grade(60) == "D"
    assert m.grade(59) == "E"
    with pytest.raises(ValueError):
        m.grade(-1)
    with pytest.raises(ValueError):
        m.grade(101)


def test_sum_to():
    assert m.sum_to(0) == 0
    assert m.sum_to(1) == 1
    assert m.sum_to(5) == 15
    assert m.sum_to(100) == 5050


def test_count_vowels_ignores_case():
    assert m.count_vowels("Hello") == 2
    assert m.count_vowels("AEIOU") == 5
    assert m.count_vowels("xyz") == 0


def test_fizzbuzz_full_sequence():
    assert m.fizzbuzz(5) == ["1", "2", "Fizz", "4", "Buzz"]
    result = m.fizzbuzz(15)
    assert result[14] == "FizzBuzz"
    assert result[2] == "Fizz"
    assert result[4] == "Buzz"
    assert result[0] == "1"


def test_find_first_even_index():
    assert m.find_first_even([1, 3, 4, 5]) == 2
    assert m.find_first_even([2, 4]) == 0
    assert m.find_first_even([1, 3, 5]) == -1
    assert m.find_first_even([]) == -1


def test_multiplication_row():
    assert m.multiplication_row(3) == ["1x3=3", "2x3=6", "3x3=9"]
    assert m.multiplication_row(0) == []


def test_is_prime():
    assert m.is_prime(2) is True
    assert m.is_prime(3) is True
    assert m.is_prime(4) is False
    assert m.is_prime(97) is True
    assert m.is_prime(1) is False
    assert m.is_prime(-7) is False
    assert m.is_prime(100) is False


def test_countdown_while():
    assert m.countdown_while(3) == [3, 2, 1]
    assert m.countdown_while(0) == []
    assert m.countdown_while(-5) == []


def test_sum_until_over():
    assert m.sum_until_over(10) == (15, 5)
    assert m.sum_until_over(0) == (1, 1)
    assert m.sum_until_over(5) == (6, 3)
