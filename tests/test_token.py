import unittest

from sanipro.token import (
    A1111Token,
    CSVToken,
    Escaper,
    format_a1111_token,
    format_csv_token,
)


class Testformat_a1111_token(unittest.TestCase):
    def test_token(self) -> None:
        test_cases = [
            (A1111Token("42", 1.0), "42"),
            (A1111Token("42", 1.1), "(42:1.1)"),
            (A1111Token("42", 1.04), "(42:1.04)"),
            (A1111Token("42", 1.05), "(42:1.05)"),
        ]

        for token, expected in test_cases:
            self.assertEqual(format_a1111_token(token), expected)


class Testformat_csv_token(unittest.TestCase):
    def test_token(self) -> None:
        delimiter = "\t"
        test_cases = [
            (CSVToken("42", 1.0), "42\t1.0"),
            (CSVToken("42", 1.1), "42\t1.1"),
        ]

        for token, expected in test_cases:
            self.assertEqual(format_csv_token(delimiter)(token), expected)


class Testformat_a1111compat_token(unittest.TestCase):
    def test_regexp_backslashes(self) -> None:
        test_cases = [("\\", r"\\"), (r"\(", r"\\("), (r"\(\)", r"\\(\\)")]

        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                self.assertEqual(Escaper.escape_backslashes(input_text), expected)

    def test_regexp_backslash_before_escaped_parentheses(self) -> None:
        test_cases = [(r"\\(", r"\\\("), (r"\\(\\)", r"\\\(\\\)")]

        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                self.assertEqual(
                    Escaper.escape_backslash_before_escaped_parentheses(input_text),
                    expected,
                )

    def test_escape_prompt(self) -> None:
        test_cases = [
            (r"1girl", r"1girl"),
            (r"re:stage!", r"re:stage!"),
            (r":3", r":3"),
        ]

        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                self.assertEqual(Escaper.escape(input_text), expected)

    def test_escaping(self) -> None:
        test_cases = [
            (r"fate \(series\)", r"fate \\\(series\\\)"),
            (r"(re:stage!:1.1)", r"(re:stage!:1.1)"),
            (r"\,", r"\\,"),
            ("\\", r"\\"),
        ]

        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                self.assertEqual(Escaper.escape(input_text), expected)

    def test_nested(self) -> None:
        test_cases = [
            (r"(1girl:1.1)", r"(1girl:1.1)"),
            (r"(fate \(series\):1.1)", r"(fate \\\(series\\\):1.1)"),
            (r"(re:stage!:1.1)", r"(re:stage!:1.1)"),
            (r"(bow, (hat:1.2):1.1)", r"(bow, (hat:1.2):1.1)"),
            (r"(bow, (:d:1.2) (hat:1.2):1.1)", r"(bow, (:d:1.2) (hat:1.2):1.1)"),
        ]

        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                self.assertEqual(Escaper.escape(input_text), expected)

    def test_signed(self) -> None:
        test_cases = [
            (r"(1girl:-1.1)", r"(1girl:-1.1)"),
            (r"(1girl:+1.1)", r"(1girl:+1.1)"),
        ]

        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                self.assertEqual(Escaper.escape(input_text), expected)
