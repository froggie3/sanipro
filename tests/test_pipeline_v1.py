import unittest

from sanipro.delimiter import Delimiter
from sanipro.pipeline_v1 import ParserV1, PromptTokenizerV1
from sanipro.token import TokenInteractive


class TestPromptTokenizerV1(unittest.TestCase):
    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)
        self.dlm = Delimiter(",", ", ")
        self.dlm_in = self.dlm.sep_input
        self.psr = ParserV1(self.dlm)
        self.tk = PromptTokenizerV1(self.psr, TokenInteractive)

    def test_add_last_comma(self):
        self.assertEqual(self.tk._add_last_comma("42", self.dlm_in), "42,")

    def test_escape_colons(self):
        self.assertEqual(self.tk._escape_colons(":", self.dlm_in), "\\:")
        self.assertEqual(
            self.tk._escape_colons("(re:stage!:1.1)", self.dlm_in), "(re\\:stage!:1.1)"
        )

    def test_strip_last_break(self):
        self.assertEqual(self.tk._strip_last_break("42\n"), "42")
        self.assertEqual(self.tk._strip_last_break("42\n \n"), "42")


class TestParserV1(unittest.TestCase):
    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)
        self.psr = ParserV1(Delimiter(",", ", "))

    def test_delete_colon(self):
        self.assertEqual(self.psr.delete_colon("re\\:stage!"), "re:stage!")


class TestPipelineV1(unittest.TestCase):
    def test_parse_prompt(self):
        dlm_in = Delimiter(",", ", ").sep_input
        f = ParserV1.parse_prompt
        cls = TokenInteractive

        self.assertEqual(f(",", cls, dlm_in), [cls("", 1.0)])  # BUG
        self.assertEqual(f(",,", cls, dlm_in), [cls("", 1.0)])  # BUG
        self.assertEqual(f(",,,", cls, dlm_in), [cls("", 1.0), cls("", 1.0)])  # BUG

        self.assertEqual(f("(,:1.1),", cls, dlm_in), [cls(",", 1.1)])  # BUG

        # test if normal emphasis works
        self.assertEqual(f("1girl,", cls, dlm_in), [cls("1girl", 1.0)])
        self.assertEqual(f("(black hair:1.1),", cls, dlm_in), [cls("black hair", 1.1)])

        # wicked characters
        self.assertEqual(f("\\:d,", cls, dlm_in), [cls("\\:d", 1.0)])
        self.assertEqual(f("(\\:3:1.2),", cls, dlm_in), [cls("\\:3", 1.2)])

        self.assertEqual(f("\\,", cls, dlm_in), [cls("\\", 1.0)])  # BUG
        self.assertEqual(f("\\(\\),", cls, dlm_in), [cls("\\(\\)", 1.0)])

        # wicked characters + emphasis
        self.assertEqual(
            f("(re\\:stage!:1.2),", cls, dlm_in), [cls("re\\:stage!", 1.2)]
        )

        # error if novelai
        with self.assertRaises(ValueError) as e:
            f("(re:stage!),", cls, dlm_in)
            self.assertEqual(e.__class__, ValueError)

        # test if backslash escaping works
        self.assertEqual(
            f("fate \\(series\\),", cls, dlm_in), [cls("fate \\(series\\)", 1.0)]
        )
        self.assertEqual(
            f("(fate \\(series\\):1.1),", cls, dlm_in), [cls("fate \\(series\\)", 1.1)]
        )

        self.assertEqual(
            f("aaa, (sailor:1.2) (hat:1.2),", cls, dlm_in),
            [cls("aaa", 1.0), cls("(sailor:1.2) (hat:1.2)", 1.0)],
        )
        self.assertEqual(
            f("(aaa, (sailor:1.2) (hat:1.2):1.3),", cls, dlm_in),
            [cls("aaa, (sailor:1.2) (hat:1.2)", 1.3)],
        )
