import logging
from typing import Union

from lib.common import Prompt, PromptInteractive, PromptNonInteractive, Sentence, Tokens, read_char

logger = logging.getLogger()


def extract_token(sentence: Sentence):
    """
    split `sentence` at commas and remove parentheses.

    >>> list(extract_token('1girl,'))
    ['1girl']
    >>> list(extract_token('(brown hair:1.2),'))
    ['brown hair:1.2']
    >>> list(extract_token('1girl, (brown hair:1.2), school uniform, smile,'))
    ['1girl', 'brown hair:1.2', 'school uniform', 'smile']
    """
    stack = []
    character_stack = []

    for character in sentence:
        match(character):
            case Tokens.PARENSIS_LEFT:
                stack.append(character)
            case Tokens.PARENSIS_RIGHT:
                stack.pop()
            case Tokens.COMMA:
                if stack:
                    read_char(character_stack, character)
                    continue
                element = "".join(character_stack).strip()
                character_stack = []
                yield element
            case _:
                read_char(character_stack, character)


def parse_line(token_combined: str, factory: Prompt) -> Prompt:
    """
    split `token_combined` into left and right sides with `:`
    when there are three or more elements, 
    the right side separated by the last colon is adopted as the strength.

    >>> from common import (PromptInteractive, PromptNonInteractive)

    >>> parse_line('brown hair:1.2', PromptInteractive)
    Prompt(name='brown hair', strength=1.2)

    >>> parse_line('1girl', PromptInteractive)
    Prompt(name='1girl', strength=1.0)

    >>> parse_line('brown:hair:1.2', PromptInteractive)
    Prompt(name='brown:hair', strength=1.2)
    """
    token = token_combined.split(Tokens.COLON)

    if not callable(factory):
        raise Exception

    prompt = factory()
    match (len(token)):
        case 1:
            prompt._name, = token
        case 2:
            prompt._name, prompt._strength = token
        case _:
            *ret, prompt._strength = token
            prompt._name = Tokens.COLON.join(ret)
    return prompt


def parse(sentence: Sentence, factory: Prompt):
    prompts = list()

    for element in extract_token(sentence):
        prompt = parse_line(element, factory)
        if isinstance(prompt, Prompt):
            prompts.append(str(prompt))

    return prompts


if __name__ == "__main__":
    import doctest
    doctest.testmod()
