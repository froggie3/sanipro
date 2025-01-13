import unittest

from sanipro.converter_context import format_a1111_token, format_csv_token
from sanipro.token import A1111Token, CSVToken


class TestTokenInteractive(unittest.TestCase):
    def test_token(self):
        test_cases = [
            (A1111Token("42", 1.0), "42"),
            (A1111Token("42", 1.1), "(42:1.1)"),
            (A1111Token("42", 1.04), "(42:1.04)"),
            (A1111Token("42", 1.05), "(42:1.05)"),
        ]

        for token, expected in test_cases:
            self.assertEqual(format_a1111_token(token), expected)


class TestTokenNonInteractive(unittest.TestCase):
    def test_token(self):
        delimiter = "\t"
        test_cases = [
            (CSVToken("42", 1.0), "42\t1.0"),
            (CSVToken("42", 1.1), "42\t1.1"),
        ]

        for token, expected in test_cases:
            self.assertEqual(format_csv_token(delimiter)(token), expected)
