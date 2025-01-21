import unittest

from sanipro.filters.fuzzysort import (
    GreedyReorderer,
    KruskalMSTReorderer,
    NaiveReorderer,
    PrimMSTReorderer,
    SequenceMatcherSimilarity,
)
from sanipro.token import A1111Token

Token = A1111Token

ORIGINAL_TOKENS = [
    Token("nanaco", 1.0),
    Token("apple", 1.0),
    Token("kiwi", 1.0),
    Token("banana", 1.0),
    Token("maple", 1.0),
]
STRATEGY = SequenceMatcherSimilarity()


class TestNaiveReorderer(unittest.TestCase):
    def test_find_optimal_order(self):
        f = NaiveReorderer(STRATEGY).find_optimal_order
        prompt = [
            Token("nanaco", 1.0),
            Token("banana", 1.0),
            Token("apple", 1.0),
            Token("maple", 1.0),
            Token("kiwi", 1.0),
        ]
        result = f(ORIGINAL_TOKENS)
        self.assertEqual(prompt, result)


class TestGreedyMSTReorderer(unittest.TestCase):
    def test_find_optimal_order(self):
        f = GreedyReorderer(STRATEGY, shuffle=False).find_optimal_order
        prompt = [
            Token("maple", 1.0),
            Token("apple", 1.0),
            Token("nanaco", 1.0),
            Token("banana", 1.0),
            Token("kiwi", 1.0),
        ]
        result = f(ORIGINAL_TOKENS)
        self.assertEqual(prompt, result)


class TestKruskalMSTReorderer(unittest.TestCase):
    def test_find_optimal_order(self):
        f = KruskalMSTReorderer(STRATEGY).find_optimal_order
        prompt = [
            Token("nanaco", 1.0),
            Token("banana", 1.0),
            Token("apple", 1.0),
            Token("maple", 1.0),
            Token("kiwi", 1.0),
        ]
        result = f(ORIGINAL_TOKENS)
        self.assertEqual(prompt, result)


class TestPrimMSTReorderer(unittest.TestCase):
    def test_find_optimal_order(self):
        f = PrimMSTReorderer(STRATEGY).find_optimal_order
        prompt = [
            Token("nanaco", 1.0),
            Token("banana", 1.0),
            Token("apple", 1.0),
            Token("maple", 1.0),
            Token("kiwi", 1.0),
        ]
        result = f(ORIGINAL_TOKENS)
        self.assertEqual(prompt, result)
