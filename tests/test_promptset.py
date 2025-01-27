import unittest

from sanipro.promptset import (
    DifferenceCalculator,
    IntersectionCalculator,
    SymmetricDifferenceCalculator,
    UnionCalculator,
)
from sanipro.token import A1111Token

T = A1111Token


class TestUnionCalculator(unittest.TestCase):
    def test_do_math(self) -> None:
        i = UnionCalculator


class TestIntersectionCalculator(unittest.TestCase):
    def test_do_math(self) -> None:
        i = IntersectionCalculator


class TestSymmetricDifferenceCalculator(unittest.TestCase):
    def test_do_math(self) -> None:
        i = SymmetricDifferenceCalculator


class TestDifferenceCalculator(unittest.TestCase):
    def test_do_math(self) -> None:
        i = DifferenceCalculator()
        test_cases = [
            (
                (
                    [T("2", 1.0), T("3", 1.0), T("4", 1.0)],
                    [T("1", 1.0), T("2", 1.0)],
                    False,
                ),
                (T("3", 1.0), T("4", 1.0)),
            ),
            (
                (
                    [T("1", 1.0), T("2", 1.0)],
                    [T("2", 1.0), T("3", 1.0), T("4", 1.0)],
                    False,
                ),
                (T("1", 1.0),),
            ),
        ]

        for token, expected in test_cases:
            a, b, reverse = token
            result = i.do_math(a, b, reverse)
            self.assertEqual(set(result), set(expected))

    def test_do_math_reversed(self) -> None:
        i = DifferenceCalculator()
        test_cases = [
            (
                (
                    [T("2", 1.0), T("3", 1.0), T("4", 1.0)],
                    [T("1", 1.0), T("2", 1.0)],
                    True,
                ),
                (T("1", 1.0),),
            )
        ]

        for token, expected in test_cases:
            a, b, reverse = token
            result = i.do_math(a, b, reverse)
            self.assertEqual(set(result), set(expected))
