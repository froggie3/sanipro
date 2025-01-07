import unittest

from sanipro.delimiter import Delimiter
from sanipro.pipeline_v1 import (
    ParserV1,
    PromptTokenizerV1,
    find_last_paren,
    parse_bad_tuple,
)
from sanipro.token import TokenInteractive


class Testparse_bad_tuple(unittest.TestCase):
    def test_parse_bad_tuple(self):
        cls = TokenInteractive
        f = parse_bad_tuple

        self.assertEqual(f("brown hair:1.2", cls), cls("brown hair", 1.2))
        self.assertEqual(f("1girl", cls), cls("1girl", 1.0))
        self.assertEqual(f("brown:hair:1.2", cls), cls("brown:hair", 1.2))
        self.assertEqual(f("brown:hair", cls), cls("brown:hair", 1.0))


class Testfind_last_paren(unittest.TestCase):
    def test_find_last_paren(self):
        f = find_last_paren

        self.assertEqual(f(r"(\),", 0, 0), None)

        self.assertEqual(f("((aba:0.9), abb:1.2),", 0, 0), 19)
        self.assertEqual(f("(ab, ((aba:0.9), baa:1.1):1.1),", 0, 0), 29)

        self.assertEqual(f(r"(fate \(series\):0.9),", 0, 0), 20)
        self.assertEqual(f(r"((fate \(series\):0.9), abb:1.2),", 0, 0), 31)


class TestPromptTokenizerV1(unittest.TestCase):
    def setUp(self) -> None:
        self.dlm = Delimiter(",", ", ")
        self.dlm_in = self.dlm.sep_input
        self.psr = ParserV1(self.dlm)
        self.token_cls = TokenInteractive
        self.tk = PromptTokenizerV1(self.psr, self.token_cls)

    def test_add_last_comma(self):
        self.assertEqual(self.tk._add_last_comma("42", self.dlm_in), "42,")

    def test_strip_last_break(self):
        self.assertEqual(self.tk._strip_last_break("42\n"), "42")
        self.assertEqual(self.tk._strip_last_break("42\n \n"), "42")


class TestParserV1(unittest.TestCase):
    def setUp(self) -> None:
        self.psr = ParserV1(Delimiter(",", ", "))

    def test_parse_prompt(self):
        dlm = Delimiter(",", ", ")
        dlm_in = dlm.sep_input
        f = ParserV1(dlm).parse_prompt
        cls = TokenInteractive

        # not a bug, but it is impossible to distinguish literal ',' and just a ',' as a delimiter
        self.assertEqual(f(",", cls, dlm_in), [cls("", 1.0)])
        self.assertEqual(f(",,", cls, dlm_in), [cls("", 1.0), cls("", 1.0)])
        self.assertEqual(
            f(",,,", cls, dlm_in), [cls("", 1.0), cls("", 1.0), cls("", 1.0)]
        )

        # not a bug
        self.assertEqual(f("(,:1.1),", cls, dlm_in), [cls(",", 1.1)])

        # using escape for parser to parse literal "delimiter"
        self.assertEqual(f(r"\,,", cls, dlm_in), [cls(r",", 1.0)])
        self.assertEqual(f(r"\,\,,", cls, dlm_in), [cls(",,", 1.0)])

        # test if normal emphasis works
        self.assertEqual(f("1girl,", cls, dlm_in), [cls("1girl", 1.0)])
        self.assertEqual(f("(black hair:1.1),", cls, dlm_in), [cls("black hair", 1.1)])

        # wicked characters
        self.assertEqual(f(r"\:d,", cls, dlm_in), [cls(":d", 1.0)])
        self.assertEqual(f(r"(\:3:1.2),", cls, dlm_in), [cls(":3", 1.2)])

        # raise error if normal character was found after a backslash
        with self.assertRaises(ValueError) as e:
            f(r"\a,", cls, dlm_in)
            self.assertEqual(e.__class__, ValueError)

        # bashslash itself
        self.assertEqual(f(r"\\,", cls, dlm_in), [cls("\\", 1.0)])

        # escaped paren -> "\(aiueo\)" -> for parser to read, should be "\\(aiueo\\)"
        self.assertEqual(f(r"\\\(series\\\),", cls, dlm_in), [cls(r"\(series\)", 1.0)])

        # wicked characters + emphasis
        self.assertEqual(f(r"(re\:stage!:1.2),", cls, dlm_in), [cls("re:stage!", 1.2)])
        self.assertEqual(
            f(r"(fate \\\(series\\\):1.2),", cls, dlm_in),
            [cls(r"fate \(series\)", 1.2)],
        )

        # error if novelai
        with self.assertRaises(ValueError) as e:
            f("(re:stage!),", cls, dlm_in)
            self.assertEqual(e.__class__, ValueError)

        # test if backslash escaping works
        self.assertEqual(
            f(r"fate \\\(series\\\),", cls, dlm_in), [cls(r"fate \(series\)", 1.0)]
        )
        self.assertEqual(
            f(r"(fate \\\(series\\\):1.1),", cls, dlm_in),
            [cls(r"fate \(series\)", 1.1)],
        )

        # test if meta paren block works
        self.assertEqual(
            f("aaa, (sailor:1.2) (hat:1.2),", cls, dlm_in),
            [cls("aaa", 1.0), cls("(sailor:1.2) (hat:1.2)", 1.0)],
        )
        self.assertEqual(
            f("(aaa, (sailor:1.2) (hat:1.2):1.3),", cls, dlm_in),
            [cls("aaa, (sailor:1.2) (hat:1.2)", 1.3)],
        )

        # test if escaping works
        self.assertEqual(
            f(r"(bba:1.2) fate \\\(series\\\),", cls, dlm_in),
            [cls(r"(bba:1.2) fate \(series\)", 1.0)],
        )
