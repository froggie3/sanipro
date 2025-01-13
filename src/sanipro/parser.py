import typing

from sanipro.abc import ParserInterface, TokenInterface
from sanipro.delimiter import Delimiter
from sanipro.mixins import ParserPropertyMixins


class UseDelimiterMixin:
    """Injects delimiter to split the prompt."""

    def __init__(self, delimiter: Delimiter) -> None:
        self._delimiter = delimiter


class NormalParser(ParserInterface, UseDelimiterMixin, ParserPropertyMixins):
    """Uses a delimiter to split the prompt."""


class CSVParser(NormalParser):
    """CSV Parser."""

    def get_token(
        self, sentence: str, token_cls: type[TokenInterface]
    ) -> typing.Generator[TokenInterface, None, None]:

        prompt = sentence.split(self._delimiter.sep_input)
        separator = self._delimiter.sep_field

        for token in prompt:
            token_name, token_weight = token.split(separator)
            yield token_cls(token_name, float(token_weight))


class InvalidSyntaxError(Exception):
    pass
