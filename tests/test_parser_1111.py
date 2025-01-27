import unittest

from sanipro.delimiter import Delimiter
from sanipro.parser import InvalidSyntaxError
from sanipro.parser_a1111 import A1111Parser
from sanipro.token import A1111Token as Token


class TestA1111Parser(unittest.TestCase):
    def setUp(self) -> None:
        dlm = Delimiter(",", ", ")
        self.parser = A1111Parser(dlm)
        self.delimiter = dlm.sep_input

    def test_basic_parsing(self) -> None:
        test_cases = [
            # test if normal emphasis works
            ("1girl,", [Token("1girl", 1.0)]),
            ("(black hair:1.1),", [Token("black hair", 1.1)]),
            # abbribiating left side of decimal point
            ("(black hair:.7),", [Token("black hair", 0.7)]),
            # weight as signed number
            ("(black hair:-.7),", [Token("black hair", -0.7)]),
            ("(black hair:-1.1),", [Token("black hair", -1.1)]),
            # not a bug, but it is impossible to distinguish literal ',' and just a ',' as a delimiter
            (",", [Token("", 1.0)]),
            (",,", [Token("", 1.0), Token("", 1.0)]),
            (",,,", [Token("", 1.0), Token("", 1.0), Token("", 1.0)]),
            # not a bug
            ("(,:1.1),", [Token(",", 1.1)]),
        ]

        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                result = self.parser.parse_prompt(input_text, Token, self.delimiter)
                self.assertEqual(result, expected)

    def test_handling_colon(self) -> None:
        test_cases = [
            (r":,", [Token(":", 1.0)]),
            (r"(::1.1),", [Token(":", 1.1)]),
            (r"(::1.1), aaa,", [Token(":", 1.1), Token("aaa", 1.0)]),
            (r"(::1.1), (::1.2),", [Token(":", 1.1), Token(":", 1.2)]),
            (r":d,", [Token(":d", 1.0)]),
            (r"(:3:1.2),", [Token(":3", 1.2)]),
            (r"(re:stage!:1.2),", [Token("re:stage!", 1.2)]),
        ]

        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                result = self.parser.parse_prompt(input_text, Token, self.delimiter)
                self.assertEqual(result, expected)

    def test_escape_characters(self) -> None:
        test_cases = [
            # using escape for parser to parse literal "delimiter"
            (r"\,,", [Token(r",", 1.0)]),
            (r"\,\,,", [Token(",,", 1.0)]),
        ]

        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                result = self.parser.parse_prompt(input_text, Token, self.delimiter)
                self.assertEqual(result, expected)

    def test_escaping_backslashes(self) -> None:
        test_cases = [
            # bashslash itself
            (r"\\,", [Token("\\", 1.0)]),
            # note: "\(series\)" will be escaped as \\, \(, series, \\, and \).
            (r"\\\(series\\\),", [Token(r"\(series\)", 1.0)]),
            (r"fate \\\(series\\\),", [Token(r"fate \(series\)", 1.0)]),
            (r"(fate \\\(series\\\):1.1),", [Token(r"fate \(series\)", 1.1)]),
        ]

        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                result = self.parser.parse_prompt(input_text, Token, self.delimiter)
                self.assertEqual(result, expected)

    def test_nested_parentheses(self) -> None:
        test_cases = [
            # test if meta paren block works
            (
                "cat, (bow:1.2) (hat:1.2),",
                [Token("cat", 1.0), Token("(bow:1.2) (hat:1.2)", 1.0)],
            ),
            (
                "(cat, (bow:1.2) (hat:1.2):1.3),",
                [Token("cat, (bow:1.2) (hat:1.2)", 1.3)],
            ),
            ("(cat, bow:1.2)\n, hat,", [Token("cat, bow", 1.2), Token("hat", 1.0)]),
            # test if escaping works
            (
                r"(bba:1.2) fate \\\(series\\\),",
                [Token(r"(bba:1.2) fate \(series\)", 1.0)],
            ),
        ]

        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                result = self.parser.parse_prompt(input_text, Token, self.delimiter)
                self.assertEqual(result, expected)

    def test_error(self) -> None:
        error_cases = [
            # raise error if normal character was found after a backslash
            (r"\a,", InvalidSyntaxError),
            # must be escaped
            ("(,", InvalidSyntaxError),
            ("),", InvalidSyntaxError),
            ("(),", InvalidSyntaxError),
            # don't escape me
            (r"\:d,", InvalidSyntaxError),
            (r"(\:3:1.2),", InvalidSyntaxError),
            (r"(re\:stage!:1.2),", InvalidSyntaxError),
            # emphasizing empty character
            ("(:1.2),", InvalidSyntaxError),
            # unfinished
            ("(aaa:1.),", InvalidSyntaxError),
            # emphasized token does not have numetical emphasis
            ("(white dress),", InvalidSyntaxError),
            ("(re:stage!),", InvalidSyntaxError),
        ]

        for input_text, error_type in error_cases:
            with self.subTest(input_text=input_text):
                try:
                    self.parser.parse_prompt(input_text, Token, self.delimiter)
                except Exception as err:
                    self.assertTrue(type(err), error_type)
