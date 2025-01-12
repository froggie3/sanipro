import unittest

from sanipro.diff import PromptDifferenceDetector
from sanipro.token import A1111Token


class TestPromptDifferenceDetector(unittest.TestCase):
    def setUp(self) -> None:
        dec = PromptDifferenceDetector
        cls = A1111Token
        a = [cls("42", 1.0), cls("43", 1.0)]
        b = [cls("42", 1.0), cls("43", 1.0)]
        self.dec = dec(a, b)  # BUG

    def test_duplicated(self):
        pass

    def test_compare(self):
        pass

    def test_judged_result(self):
        pass

    def test_parcentage(self):
        pass
