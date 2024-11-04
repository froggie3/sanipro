import logging

from .abc import TokenInterface

logger = logging.getLogger()


class Token(TokenInterface):
    def __init__(self, name: str, strength: float) -> None:
        self._name = name
        self._strength = float(strength)
        self._delimiter = None

    @property
    def name(self):
        return self._name

    @property
    def strength(self):
        return self._strength

    @property
    def length(self):
        return len(self.name)

    def replace(self, replace: str):
        return type(self)(replace, self._strength)

    def __repr__(self):
        items = (f"{v!r}" for v in (self.name, self.strength))
        return "{}({})".format(type(self).__name__, f"{Tokens.COMMA} ".join(items))


class TokenInteractive(Token):
    def __init__(self, name: str, strength: float):
        Token.__init__(self, name, strength)
        self._delimiter = ":"

    def __str__(self):
        if self.strength != 1.0:
            return "({}{}{:.1f})".format(self.name, self._delimiter, self.strength)
        return self.name


class TokenNonInteractive(Token):
    def __init__(self, name: str, strength: float):
        Token.__init__(self, name, strength)
        self._delimiter = "\t"

    def __str__(self):
        return "{}{}{.2f}".format(self.strength, self._delimiter, self.name)


class Tokens:
    PARENSIS_LEFT = "("
    PARENSIS_RIGHT = ")"
    COLON = ":"
    COMMA = ","
    SPACE = " "


# parser_v2 will not do anything more than parse for now
USE_PARSER_V2 = False

if USE_PARSER_V2:
    from . import parser_v2 as parser
else:
    from . import parser_v1 as parser

get_token = parser.get_token

if __name__ == "__main__":
    import doctest

    doctest.testmod()
