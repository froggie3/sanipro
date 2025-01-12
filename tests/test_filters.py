import unittest

from sanipro.filters.exclude import ExcludeCommand
from sanipro.filters.mask import MaskCommand
from sanipro.filters.roundup import RoundUpCommand
from sanipro.filters.translate import TranslateTokenTypeCommand
from sanipro.token import A1111Token, CSVToken

Token = A1111Token

prompt = (
    Token("open mouth", 1.0),
    Token("long sleeves", 1.0),
    Token("school uniform", 1.0),
    Token("solo", 1.0),
    Token("white background", 1.0),
    Token("red hair", 1.0),
    Token("jacket", 1.0),
    Token("one side up", 1.0),
    Token("happy", 1.0),
    Token("long hair", 1.0),
    Token("shirt", 1.0),
    Token("1girl", 1.0),
    Token("simple background", 1.0),
    Token("looking at viewer", 1.0),
    Token("yellow eyes", 1.0),
    Token("smile", 1.0),
    Token(":d", 1.25892541179),
    Token("bow", 1.0),
    Token("hair between eyes", 1.0),
)


class TestExcludeCommand(unittest.TestCase):
    def test_execute_prompt(self):
        self.inst = ExcludeCommand(["background"])
        f = self.inst.execute_prompt
        self.assertNotIn(Token("simple background", 1.0), f(prompt))
        self.assertNotIn(Token("white background", 1.0), f(prompt))


class TestMaskCommand(unittest.TestCase):
    def test_execute_prompt(self):
        self.inst = MaskCommand(["background"], "__REPLACE__")
        f = self.inst.execute_prompt

        self.assertNotIn(Token("simple background", 1.0), f(prompt))
        self.assertNotIn(Token("white background", 1.0), f(prompt))

        count = sum(1 for token in f(prompt) if "__REPLACE__" in token.name)
        self.assertEqual(count, 2)


class TestRoundUpCommand(unittest.TestCase):
    def test_execute_prompt(self):
        self.inst = RoundUpCommand(2)
        f = self.inst.execute_prompt

        self.assertIn(Token(":d", 1.26), f(prompt))


class TestTranslateTokenCOmmand(unittest.TestCase):
    def test_execute_prompt(self):
        token_type = CSVToken
        self.inst = TranslateTokenTypeCommand(token_type)
        f = self.inst.execute_prompt

        self.assertTrue(token_type("1girl", 1.0), f([Token("1girl", 1.0)]))
