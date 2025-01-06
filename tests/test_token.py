import unittest

from sanipro.token import TokenInteractive, TokenNonInteractive


class TestTokenInteractive(unittest.TestCase):
    def test_token(self):
        self.assertEqual(TokenInteractive("42", 1.0).__str__(), "42")
        self.assertEqual(TokenInteractive("42", 1.1).__str__(), "(42:1.1)")
        self.assertEqual(TokenInteractive("42", 1.04).__str__(), "(42:1.04)")
        self.assertEqual(TokenInteractive("42", 1.05).__str__(), "(42:1.05)")


class TestTokenNonInteractive(unittest.TestCase):
    def test_token(self):
        self.assertEqual(TokenNonInteractive("42", 1.0).__str__(), "42\t1.0")
        self.assertEqual(TokenNonInteractive("42", 1.1).__str__(), "42\t1.1")
