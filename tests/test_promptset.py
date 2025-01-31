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
    def setUp(self) -> None:
        self.calculator = UnionCalculator()

    def test_do_math(self) -> None:
        test_cases = [
            (
                ([T("2", 1.0), T("3", 1.0), T("4", 1.0)], [T("1", 1.0), T("2", 1.0)]),
                (T("1", 1.0), T("2", 1.0), T("3", 1.0), T("4", 1.0)),
            )
        ]

        for token, expected in test_cases:
            a, b = token
            result = self.calculator.do_math(a, b)
            self.assertEqual(set(result), set(expected))


class TestIntersectionCalculator(unittest.TestCase):
    def setUp(self) -> None:
        self.calculator = IntersectionCalculator()

    def test_do_math(self) -> None:
        test_cases = [
            (
                ([T("2", 1.0), T("3", 1.0), T("4", 1.0)], [T("1", 1.0), T("2", 1.0)]),
                (T("2", 1.0),),
            )
        ]

        for token, expected in test_cases:
            a, b = token
            result = self.calculator.do_math(a, b)
            self.assertEqual(set(result), set(expected))


class TestSymmetricDifferenceCalculator(unittest.TestCase):
    def setUp(self) -> None:
        self.calculator = SymmetricDifferenceCalculator()

    def test_do_math(self) -> None:
        test_cases = [
            (
                ([T("2", 1.0), T("3", 1.0), T("4", 1.0)], [T("1", 1.0), T("2", 1.0)]),
                (T("1", 1.0), T("3", 1.0), T("4", 1.0)),
            )
        ]

        for token, expected in test_cases:
            a, b = token
            result = self.calculator.do_math(a, b)
            self.assertEqual(set(result), set(expected))


class TestDifferenceCalculator(unittest.TestCase):
    def test_do_math(self) -> None:
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
            result = DifferenceCalculator(reverse).do_math(a, b)
            self.assertEqual(set(result), set(expected))

    def test_do_math_reversed(self) -> None:
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
            result = DifferenceCalculator(reverse).do_math(a, b)
            self.assertEqual(set(result), set(expected))
