import unittest

from sanipro.filters.fuzzysort import (
    GreedyReorderer,
    KruskalMSTReorderer,
    NaiveReorderer,
    PrimMSTReorderer,
    SequenceMatcherSimilarity,
)
from sanipro.token_prompt import A1111Token

Token = A1111Token


class TestNaiveReorderer(unittest.TestCase):
    def setUp(self) -> None:
        self.strategy = SequenceMatcherSimilarity()
        self.reorderer = NaiveReorderer(self.strategy)

    def test_find_optimal_order(self) -> None:
        f = self.reorderer.find_optimal_order
        original_tokens = [
            Token("nanaco", 1.0),
            Token("apple", 1.0),
            Token("kiwi", 1.0),
            Token("banana", 1.0),
            Token("maple", 1.0),
        ]

        prompt = [
            Token("nanaco", 1.0),
            Token("banana", 1.0),
            Token("apple", 1.0),
            Token("maple", 1.0),
            Token("kiwi", 1.0),
        ]

        result = f(original_tokens)
        self.assertEqual(prompt, result)


class TestGreedyReorderer(unittest.TestCase):
    def setUp(self) -> None:
        self.strategy = SequenceMatcherSimilarity()
        self.reorderer = GreedyReorderer(self.strategy, shuffle=False)

    def test_find_optimal_order(self) -> None:
        f = self.reorderer.find_optimal_order
        original_tokens = [
            Token("nanaco", 1.0),
            Token("apple", 1.0),
            Token("kiwi", 1.0),
            Token("banana", 1.0),
            Token("maple", 1.0),
        ]

        prompt = [
            Token("maple", 1.0),
            Token("apple", 1.0),
            Token("nanaco", 1.0),
            Token("banana", 1.0),
            Token("kiwi", 1.0),
        ]

        result = f(original_tokens)
        self.assertEqual(prompt, result)


class TestKruskalMSTReorderer(unittest.TestCase):
    def setUp(self) -> None:
        self.strategy = SequenceMatcherSimilarity()
        self.reorderer = KruskalMSTReorderer(self.strategy)

    def test_find_optimal_order(self) -> None:
        f = self.reorderer.find_optimal_order
        original_tokens = [
            Token("nanaco", 1.0),
            Token("apple", 1.0),
            Token("kiwi", 1.0),
            Token("banana", 1.0),
            Token("maple", 1.0),
        ]

        prompt = [
            Token("nanaco", 1.0),
            Token("banana", 1.0),
            Token("apple", 1.0),
            Token("maple", 1.0),
            Token("kiwi", 1.0),
        ]

        result = f(original_tokens)
        self.assertEqual(prompt, result)


class TestPrimMSTReorderer(unittest.TestCase):
    def setUp(self) -> None:
        self.strategy = SequenceMatcherSimilarity()
        self.reorderer = PrimMSTReorderer(self.strategy)

    def test_find_optimal_order(self) -> None:
        f = self.reorderer.find_optimal_order
        original_tokens = [
            Token("nanaco", 1.0),
            Token("apple", 1.0),
            Token("kiwi", 1.0),
            Token("banana", 1.0),
            Token("maple", 1.0),
        ]

        prompt = [
            Token("nanaco", 1.0),
            Token("banana", 1.0),
            Token("apple", 1.0),
            Token("maple", 1.0),
            Token("kiwi", 1.0),
        ]

        result = f(original_tokens)
        self.assertEqual(prompt, result)
