import unittest

from sanipro.token import A1111Token, CSVToken


class TestTokenInteractive(unittest.TestCase):
    def test_token(self):
        self.assertEqual(A1111Token("42", 1.0).__str__(), "42")
        self.assertEqual(A1111Token("42", 1.1).__str__(), "(42:1.1)")
        self.assertEqual(A1111Token("42", 1.04).__str__(), "(42:1.04)")
        self.assertEqual(A1111Token("42", 1.05).__str__(), "(42:1.05)")


class TestTokenNonInteractive(unittest.TestCase):
    def test_token(self):
        self.assertEqual(CSVToken("42", 1.0).__str__(), "42\t1.0")
        self.assertEqual(CSVToken("42", 1.1).__str__(), "42\t1.1")
