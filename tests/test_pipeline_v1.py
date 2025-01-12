import unittest

from sanipro.delimiter import Delimiter
from sanipro.pipeline_v1 import (
    A1111Parser,
    A1111Tokenizer,
    InvalidSyntaxError,
    find_last_paren,
    parse_bad_tuple,
)
from sanipro.token import A1111Token as Token


class Testparse_bad_tuple(unittest.TestCase):
    def test_emphasis(self):
        test_cases = [
            ("(white dress:1.2)", Token("white dress", 1.2)),
            ("(re:stage!:1.2)", Token("re:stage!", 1.2)),
            (
                "(aaa, (sailor:1.2) (hat:1.2):1.3)",
                Token("aaa, (sailor:1.2) (hat:1.2)", 1.3),
            ),
            ("(::1.2)", Token(":", 1.2)),
        ]

        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                self.assertEqual(parse_bad_tuple(input_text, Token), expected)


class Testfind_last_paren(unittest.TestCase):
    def test_find_last_paren(self):
        test_cases = [
            (r"(\),", None),
            # a
            ("((aba:0.9), abb:1.2),", 19),
            ("(ab, ((aba:0.9), baa:1.1):1.1),", 29),
            # b
            (r"(fate \(series\):0.9),", 20),
            (r"((fate \(series\):0.9), abb:1.2),", 31),
        ]

        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                self.assertEqual(find_last_paren(input_text, 0, 0), expected)


class TestPromptTokenizerV1(unittest.TestCase):
    def setUp(self) -> None:
        self.dlm = Delimiter(",", ", ")
        self.dlm_in = self.dlm.sep_input
        self.psr = A1111Parser(self.dlm)
        self.tk = A1111Tokenizer(self.psr, Token)

    def test_add_last_comma(self):
        self.assertEqual(self.tk._add_last_comma("42", self.dlm_in), "42,")

    def test_strip_last_break(self):
        self.assertEqual(self.tk._strip_last_break("42\n"), "42")
        self.assertEqual(self.tk._strip_last_break("42\n \n"), "42")


class TestParserV1(unittest.TestCase):
    def setUp(self) -> None:
        self.psr = A1111Parser(Delimiter(",", ", "))
        dlm = Delimiter(",", ", ")
        self.parser = A1111Parser(dlm)
        self.delimiter = dlm.sep_input

    def test_basic_parsing(self):
        test_cases = [
            # test if normal emphasis works
            ("1girl,", [Token("1girl", 1.0)]),
            ("(black hair:.7),", [Token("black hair", 0.7)]),
            ("(black hair:1.1),", [Token("black hair", 1.1)]),
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

    def test_handling_colon(self):
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

    def test_escape_characters(self):
        test_cases = [
            # using escape for parser to parse literal "delimiter"
            (r"\,,", [Token(r",", 1.0)]),
            (r"\,\,,", [Token(",,", 1.0)]),
        ]

        for input_text, expected in test_cases:
            with self.subTest(input_text=input_text):
                result = self.parser.parse_prompt(input_text, Token, self.delimiter)
                self.assertEqual(result, expected)

    def test_escaping_backslashes(self):
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

    def test_nested_parentheses(self):
        test_cases = [
            # test if meta paren block works
            (
                "aaa, (sailor:1.2) (hat:1.2),",
                [Token("aaa", 1.0), Token("(sailor:1.2) (hat:1.2)", 1.0)],
            ),
            (
                "(aaa, (sailor:1.2) (hat:1.2):1.3),",
                [Token("aaa, (sailor:1.2) (hat:1.2)", 1.3)],
            ),
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

    def test_error(self):
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
