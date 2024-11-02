import logging
from typing import Any, Callable, NamedTuple, Type, TypedDict

from . import parser
from .abc import PromptInterface

logger = logging.getLogger()


class FuncConfig(TypedDict):
    # func: Callable[...]
    func: Callable
    kwargs: dict[str, Any]


class Delimiter(NamedTuple):
    sep_input: str
    sep_output: str

    @classmethod
    def create_builder(cls, input: str, output: str) -> "SentenceBuilder":
        return SentenceBuilder(cls(input, output))


class SentenceBuilder:
    def __init__(self, delimiter: Delimiter):
        self.pre_funcs = []
        self.funcs: list[FuncConfig] = []
        self.tokens = []
        self.delimiter = delimiter

        def add_last(sentence: str) -> str:
            """Add the delimiter character to the last part of the sentence,
            this is useful for simplicity of implementation"""
            if not sentence.endswith((delimiter.sep_input)):
                sentence += delimiter.sep_input
            return sentence

        self.append_pre_hook(add_last)

    def __str__(self) -> str:
        lines = []
        delim = self.delimiter.sep_output
        for token in self.tokens:
            lines.append(str(token))

        return delim.join(lines)

    def apply(
        self, prompts: list[PromptInterface], funcs: list[FuncConfig] = []
    ) -> "SentenceBuilder":
        # marge!
        self.funcs = [*set([*self.funcs, *funcs])]
        for func in self.funcs:
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

        for element in parser.extract_token(sentence, self.delimiter.sep_input):
            logger.debug(f"{element=}")
            prompt = parser.parse_line(element, factory)
            prompts.append(prompt)

        return prompts

    def append_pre_hook(self, func) -> None:
        self.pre_funcs.append(func)

    def append_hook(self, func) -> None:
        self.funcs.append(func)


if __name__ == "__main__":
    import doctest

    doctest.testmod()
