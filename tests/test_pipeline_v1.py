import unittest

from sanipro.delimiter import Delimiter
from sanipro.parser_a1111 import A1111Parser, find_last_paren, parse_bad_tuple
from sanipro.pipeline_v1 import A1111Tokenizer
from sanipro.token import A1111Token as Token


class Testparse_bad_tuple(unittest.TestCase):
    def test_emphasis(self):
        test_cases = [
            ("(white dress:1.2)", Token("white dress", 1.2)),
            ("(white dress:+1.2)", Token("white dress", 1.2)),
            ("(white dress:-1.2)", Token("white dress", -1.2)),
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
