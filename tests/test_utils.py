import unittest

from sanipro.token import A1111Token
from sanipro.utils import round_token_weight


class Testround_token_weight(unittest.TestCase):
    def test_round_token_weight(self):
        self.assertEqual(
            round_token_weight(A1111Token("aaaa", 3.14159265), 2),
            A1111Token("aaaa", 3.14),
        )
        self.assertEqual(
            round_token_weight(A1111Token("aaaa", 3.14159265), 5),
            A1111Token("aaaa", 3.14159),
        )
