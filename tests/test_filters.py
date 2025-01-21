import unittest

from sanipro.filters.exclude import ExcludeCommand
from sanipro.filters.mask import MaskCommand
from sanipro.filters.reset import ResetCommand
from sanipro.filters.roundup import RoundUpCommand
from sanipro.filters.sort import SortCommand
from sanipro.filters.sort_all import SortAllCommand
from sanipro.filters.translate import TranslateTokenTypeCommand
from sanipro.filters.unique import UniqueCommand
from sanipro.filters.utils import (
    sort_by_length,
    sort_by_ord_sum,
    sort_by_weight,
    sort_lexicographically,
)
from sanipro.token import A1111Token, CSVToken

Token = A1111Token

PROMPT = (
    Token("white background", 1.0),
    Token("red hair", 1.0),
    Token("jacket", 1.0),
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
        f = ExcludeCommand(["background"]).execute_prompt

        self.assertNotIn(Token("simple background", 1.0), f(PROMPT))
        self.assertNotIn(Token("white background", 1.0), f(PROMPT))


@unittest.skip("test later")
class TestSimilarCommand(unittest.TestCase):
    def test_execute_prompt(self):
        pass


class TestMaskCommand(unittest.TestCase):
    def test_execute_prompt(self):
        f = MaskCommand(["background"], "__REPLACE__").execute_prompt

        self.assertNotIn(Token("simple background", 1.0), f(PROMPT))
        self.assertNotIn(Token("white background", 1.0), f(PROMPT))

        count = sum(1 for token in f(PROMPT) if "__REPLACE__" in token.name)
        self.assertEqual(count, 2)


class TestResetCommand(unittest.TestCase):
    def test_execute_prompt(self):
        tests = [
            (None, [Token("shift", 1.0)], [Token("shift", 1.0)]),
            (1.1, [Token("solo", 0.876)], [Token("solo", 1.1)]),
        ]

        for new_value, token, expected in tests:
            f = ResetCommand(new_value).execute_prompt
            self.assertEqual(expected, f(token))


class TestRoundUpCommand(unittest.TestCase):
    def test_execute_prompt(self):
        f = RoundUpCommand(2).execute_prompt

        self.assertIn(Token(":d", 1.26), f(PROMPT))


class TestSortAllCommand(unittest.TestCase):
    def test_execute_prompt(self):
        FIXED_PROMPT = [
            Token("shirt", 1.3),
            Token("one side up", 1.0),
            Token("long hair", 1.2),
            Token("happy", 1.1),
        ]
        tests = [
            (
                sort_lexicographically,
                [
                    Token("happy", 1.1),
                    Token("long hair", 1.2),
                    Token("one side up", 1.0),
                    Token("shirt", 1.3),
                ],
            ),
            (
                sort_by_weight,
                [
                    Token("one side up", 1.0),
                    Token("happy", 1.1),
                    Token("long hair", 1.2),
                    Token("shirt", 1.3),
                ],
            ),
            (
                sort_by_length,
                [
                    Token("shirt", 1.3),
                    Token("happy", 1.1),
                    Token("long hair", 1.2),
                    Token("one side up", 1.0),
                ],
            ),
            (
                sort_by_ord_sum,
                [
                    Token("happy", 1.1),
                    Token("shirt", 1.3),
                    Token("long hair", 1.2),
                    Token("one side up", 1.0),
                ],
            ),
        ]

        for func, expected in tests:
            with self.subTest(funcname=func.__name__, reversed=False):
                f = SortAllCommand(func).execute_prompt
                self.assertEqual(expected, f(FIXED_PROMPT))


class TestSortCommand(unittest.TestCase):
    def test_execute_prompt(self):
        tests = (
            (
                [
                    Token("shirt", 1.3),
                    Token("shirt", 1.0),
                    Token("shirt", 1.2),
                    Token("happy", 1.1),
                ],
                [
                    Token("shirt", 1.0),
                    Token("shirt", 1.2),
                    Token("shirt", 1.3),
                    Token("happy", 1.1),
                ],
            ),
        )

        for test, expected in tests:
            f = SortCommand(reverse=False).execute_prompt
            self.assertEqual(expected, f(test))


class TestUniqueCommand(unittest.TestCase):
    def test_execute_prompt(self):
        tests = (
            (
                False,
                [
                    Token("shirt", 1.3),
                    Token("shirt", 1.0),
                    Token("shirt", 1.2),
                    Token("happy", 1.1),
                ],
                [Token("shirt", 1.0), Token("happy", 1.1)],
            ),
            (
                True,
                [
                    Token("shirt", 1.3),
                    Token("shirt", 1.0),
                    Token("shirt", 1.2),
                    Token("happy", 1.1),
                ],
                [Token("shirt", 1.3), Token("happy", 1.1)],
            ),
        )

        for is_reversed, test, expected in tests:
            with self.subTest(reverse=is_reversed):
                f = UniqueCommand(reverse=is_reversed).execute_prompt
                self.assertEqual(expected, f(test))


class TestTranslateTokenCommand(unittest.TestCase):
    def test_execute_prompt(self):
        token_type = CSVToken
        f = TranslateTokenTypeCommand(token_type).execute_prompt

        self.assertTrue(token_type("1girl", 1.0), f([Token("1girl", 1.0)]))
