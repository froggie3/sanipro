import logging
import re
from pprint import pprint
from typing import Type

from . import utils
from .abc import TokenInterface
from .parser import Tokens

logger = logging.getLogger()

debug_fp = utils.BufferingLoggerWriter(logger, logging.DEBUG)


def extract_token(sentence: str, delimiter: str) -> list[str]:
    """
    split `sentence` at commas and remove parentheses.

    >>> list(extract_token('1girl,'))
    ['1girl']

    >>> list(extract_token('(brown hair:1.2),'))
    ['brown hair:1.2']

    >>> list(extract_token('\(foo\)'))
    ['\\(foo\\)']

    >>> list(extract_token('1girl, (brown hair:1.2), school uniform, smile,'))
    ['1girl', 'brown hair:1.2', 'school uniform', 'smile']
    """
    # final product
    product = []

    parenthesis: list[int] = []

    # consumed chararater will be accumurated before next ','
    partial = []

    index = 0
    while index < len(sentence):

        if sentence[index] == Tokens.PARENSIS_LEFT:
            if index > 0:
                if sentence[index - 1] == Tokens.BACKSLASH:
                    partial.append(sentence[index])
            else:
                parenthesis.append(index)
            index += 1

        elif sentence[index] == Tokens.PARENSIS_RIGHT:
            if index > 0:
                if sentence[index - 1] == Tokens.BACKSLASH:
                    partial.append(sentence[index])
            elif parenthesis:
                parenthesis.pop()
            index += 1

        elif sentence[index] == delimiter:
            if parenthesis:
                partial.append(sentence[index])
            else:
                element = "".join(partial).strip()
                partial.clear()
                product.append(element)
            index += 1

        else:
            partial.append(sentence[index])
            index += 1

    if parenthesis:
        first_parenthesis_index = parenthesis[0]
        raise ValueError(
            f"first unclosed parenthesis was found after {sentence[0:first_parenthesis_index]!r}"
        )

    return product


def parse_line(
    token_combined: str, token_factory: Type[TokenInterface]
) -> TokenInterface:
    """
    split `token_combined` into left and right sides with `:`
    when there are three or more elements,
    the right side separated by the last colon is adopted as the strength.

    >>> from lib.common import PromptInteractive, PromptNonInteractive

    >>> parse_line('brown hair:1.2', PromptInteractive)
    PromptInteractive('brown hair', 1.2)

    >>> parse_line('1girl', PromptInteractive)
    PromptInteractive('1girl', 1.0)

    >>> parse_line('brown:hair:1.2', PromptInteractive)
    PromptInteractive('brown:hair', 1.2)

    >>> parse_line('brown:hair', PromptInteractive)
    PromptInteractive('brown:hair', 1.0)
    """

    name_pattern = r"(.*?)"
    weight_pattern = r"(\d+(?:\.\d+)?)"

    pattern = rf"^{name_pattern}(?::{weight_pattern})?$"

    m = re.match(pattern, token_combined)

    if m:
        return token_factory(m.group(1), float(m.group(2) or 1.0))

    raise Exception(f"no matched string for {token_combined!r}")


def get_token(
    token_factory: Type[TokenInterface], sentence: str, delimiter: str | None = None
):
    if delimiter is not None:
        for element in extract_token(sentence, delimiter):
            yield parse_line(element, token_factory)
