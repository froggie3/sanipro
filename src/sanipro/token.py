import re
from typing import Callable

from sanipro.abc import TokenInterface
from sanipro.compatible import Self


class Token(TokenInterface):
    _delimiter: str

    def __init__(self, name: str, weight: float) -> None:
        self._name = name
        self._weight = float(weight)

    @property
    def name(self) -> str:
        return self._name

    @property
    def weight(self) -> float:
        return self._weight

    @property
    def length(self) -> int:
        return len(self.name)

    def replace(
        self, *, new_name: str | None = None, new_weight: float | None = None
    ) -> Self:
        if new_name is None:
            new_name = self._name
        if new_weight is None:
            new_weight = self._weight

        return type(self)(new_name, new_weight)

    def __repr__(self) -> str:
        items = (f"{v!r}" for v in (self.name, self.weight))
        return "{}({})".format(type(self).__name__, f", ".join(items))

    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            raise TypeError
        return self._name == other._name and self._weight == other._weight

    def __hash__(self) -> int:
        return hash((self._name, self._weight))


class A1111Token(Token):
    def __init__(self, name: str, weight: float) -> None:
        Token.__init__(self, name, weight)


class CSVToken(Token):
    def __init__(self, name: str, weight: float) -> None:
        Token.__init__(self, name, weight)


def format_a1111_token(token: A1111Token) -> str:
    """Callback function to format a A1111Token."""

    if token.weight != 1.0:
        return f"({token.name}:{token.weight})"

    return token.name


class Escaper:
    backslashes = re.compile(r"([\\])")
    backslash_before_escaped_parentheses = re.compile(r"(\\[\(\)])")

    @staticmethod
    def escape_backslashes(prompt_name: str):
        """Escapes a backslash which possibly allows another backslash
        comes after it.

        e.g. `\\( \\) ===> \\\\( \\\\)`"""

        return re.sub(Escaper.backslashes, r"\\\g<1>", prompt_name)

    @staticmethod
    def escape_backslash_before_escaped_parentheses(prompt_name: str):
        """Escapes another backslash before the escaped parentheses.

        e.g. `\\\\( \\\\) ===> \\\\\\( \\\\\\)`"""

        return re.sub(
            Escaper.backslash_before_escaped_parentheses, r"\\\g<1>", prompt_name
        )

    @staticmethod
    def escape(prompt_name: str) -> str:
        """Escape prompt."""

        prompt_name = Escaper.escape_backslashes(prompt_name)
        prompt_name = Escaper.escape_backslash_before_escaped_parentheses(prompt_name)

        return prompt_name


def format_a1111_compat_token(token: A1111Token) -> str:
    """Callback function to format a A1111Token."""

    token_name = Escaper.escape(token.name)

    if token.weight != 1.0:
        return f"({token_name}:{token.weight})"

    return token_name


def format_csv_token(field_separator: str) -> Callable:
    """Callback function to format a CSVToken."""

    def f(token: CSVToken) -> str:
        return f"{token.name}{field_separator}{token.weight}"

    return f
