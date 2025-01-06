import typing

from sanipro.abc import ParserInterface, TokenInterface
from sanipro.delimiter import Delimiter


class UseDelimiterMixin:
    """Injects delimiter to split the prompt."""

    def __init__(self, delimiter: Delimiter) -> None:
        self._delimiter = delimiter


class NormalParser(ParserInterface, UseDelimiterMixin):
    """Uses a delimiter to split the prompt."""


class DummyParser(NormalParser):
    def get_token(
        self, token_cls: type[TokenInterface], sentence: str
    ) -> typing.Generator[TokenInterface, None, None]:
        return (
            token_cls(element.strip(), 1.0)
            for element in sentence.strip().split(self._delimiter.sep_input)
        )


if __name__ == "__main__":
    import doctest

    doctest.testmod()
