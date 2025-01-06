import unittest

from sanipro.diff import PromptDifferenceDetector
from sanipro.token import TokenInteractive


class TestPromptDifferenceDetector(unittest.TestCase):
    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)
        dec = PromptDifferenceDetector
        cls = TokenInteractive
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
