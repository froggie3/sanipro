import logging
from typing import Any, Callable, Generator, NamedTuple, Type, TypedDict

from .common import PromptInterface, Tokens

logger = logging.getLogger()


class FuncConfig(TypedDict):
    # func: Callable[...]
    func: Callable
    kwargs: dict[str, Any]


def consume(stack: list, char: str) -> None:
    """Consumes characters and add them to the stack"""
    stack.append(char)


def extract_token(sentence: str, delim=Tokens.COMMA) -> Generator[str, None, None]:
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
        if character == Tokens.PARENSIS_LEFT:
            stack.append(character)
        elif character == Tokens.PARENSIS_RIGHT:
            stack.pop()
        elif character == delim:
            if stack:
                consume(character_stack, character)
                continue
            element = "".join(character_stack).strip()
            character_stack.clear()
            yield element
        else:
            consume(character_stack, character)


def parse_line(token_combined: str, factory: Type[PromptInterface]) -> PromptInterface:
    """
    split `token_combined` into left and right sides with `:`
    when there are three or more elements,
    the right side separated by the last colon is adopted as the strength.

    >>> from lib.common import PromptInteractive, PromptNonInteractive

    >>> parse_line('brown hair:1.2', PromptInteractive)
    PromptInteractive(_name='brown hair', _strength='1.2', _delimiter=':')

    >>> parse_line('1girl', PromptInteractive)
    PromptInteractive(_name='1girl', _strength='1.0', _delimiter=':')

    >>> parse_line('brown:hair:1.2', PromptInteractive)
    PromptInteractive(_name='brown:hair', _strength='1.2', _delimiter=':')
    """
    token = token_combined.split(Tokens.COLON)

    match (len(token)):
        case 1:
            name, *_ = token
            return factory(name, "1.0")
        case 2:
            name, strength, *_ = token
            return factory(name, strength)
        case _:
            *ret, strength = token
            name = Tokens.COLON.join(ret)
            return factory(name, strength)


class Delimiter(NamedTuple):
    sep_input: str
    sep_output: str

    @classmethod
    def create_builder(cls, input: str, output: str) -> "SentenceBuilder":
        return SentenceBuilder(cls(input, output))


class SentenceBuilder:
    def __init__(self, delimiter: Delimiter):
        self.pre_funcs = []
        self.tokens = []
        self.delimiter = delimiter

        def add_last(sentence: str):
            """Add the delimiter character to the last part of the sentence,
            this is useful for simplicity of implementation"""
            if not sentence.endswith((delimiter.sep_input)):
                sentence += delimiter.sep_input
            return sentence

        self.add_hook(add_last)

    def __str__(self):
        lines = []
        delim = self.delimiter.sep_output
        for token in self.tokens:
            lines.append(str(token))

        return delim.join(lines)

    def apply(
        self, prompts: list[PromptInterface], funcs: list[FuncConfig]
    ) -> "SentenceBuilder":
        for func in funcs:
            prompts = func["func"](prompts, **func["kwargs"])
        self.tokens = prompts
        return self

    def parse(
        self, sentence: str, factory: Type[PromptInterface]
    ) -> list[PromptInterface]:
        prompts = []

        # executes hooks bound
        for hook in self.pre_funcs:
            sentence = hook(sentence)

        for element in extract_token(sentence, self.delimiter.sep_input):
            prompt = parse_line(element, factory)
            prompts.append(prompt)

        return prompts

    def add_hook(self, func):
        self.pre_funcs.append(func)


if __name__ == "__main__":
    import doctest

    doctest.testmod()
