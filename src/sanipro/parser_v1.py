import logging
from typing import Type

from .abc import TokenInterface
from .parser import Tokens

logger = logging.getLogger()


def extract_token(sentence: str, delimiter: str) -> list[str]:
    """
    split `sentence` at commas and remove parentheses.

    >>> list(extract_token('1girl,'))
    ['1girl']
    >>> list(extract_token('(brown hair:1.2),'))
    ['brown hair:1.2']
    >>> list(extract_token('1girl, (brown hair:1.2), school uniform, smile,'))
    ['1girl', 'brown hair:1.2', 'school uniform', 'smile']
    """

    product = []
    parenthesis = []
    character_stack = []

    for index, character in enumerate(sentence):
        if character == Tokens.PARENSIS_LEFT:
            parenthesis.append(index)
        elif character == Tokens.PARENSIS_RIGHT:
            parenthesis.pop()
        elif character == delimiter:
            if parenthesis:
                character_stack.append(character)
                continue
            element = "".join(character_stack).strip()
            character_stack.clear()
            product.append(element)
        else:
            character_stack.append(character)

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
    """
    token = token_combined.split(Tokens.COLON)
    token_length = len(token)

    match (token_length):
        case 1:
            name, *_ = token
            return token_factory(name, 1.0)
        case 2:
            name, regex_strength, *_ = token
            return token_factory(name, float(regex_strength))
        case _:
            *ret, regex_strength = token
            name = Tokens.COLON.join(ret)
            return token_factory(name, float(regex_strength))


def get_token(
    token_factory: Type[TokenInterface], sentence: str, delimiter: str | None = None
):
    if delimiter is not None:
        for element in extract_token(sentence, delimiter):
            yield parse_line(element, token_factory)
