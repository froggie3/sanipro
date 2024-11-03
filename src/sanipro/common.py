import logging
from typing import Any, Callable, NamedTuple, Type

from . import parser
from .abc import TokenInterface

logger = logging.getLogger()


class FuncConfig(NamedTuple):
    # func: Callable[...]
    func: Callable
    kwargs: tuple[tuple[str, Any], ...]


class Delimiter(NamedTuple):
    sep_input: str
    sep_output: str

    @classmethod
    def create_builder(cls, input: str, output: str) -> "PromptBuilder":
        return PromptBuilder(cls(input, output))


class PromptBuilder:
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

    def map_token(self, attr: str, func: Callable) -> None:
        for token in self.tokens:
            val = getattr(token, attr)
            val = func(val)
            setattr(token, attr, val)

    def apply(
        self, prompts: list[TokenInterface], funcs: list[FuncConfig] | None = None
    ) -> "PromptBuilder":
        """sequentially applies the filters."""
        if funcs is None:
            funcs = []
        # marge!
        self.funcs = [*set([*self.funcs, *funcs])]
        for func in self.funcs:
            prompts = func.func(prompts, **dict(func.kwargs))
        self.tokens = prompts
        return self

    def parse(
        self, sentence: str, token_factory: Type[TokenInterface], auto_apply=False
    ) -> list[TokenInterface]:
        prompts = []

        # executes hooks bound
        for hook in self.pre_funcs:
            sentence = hook(sentence)

        for element in parser.extract_token(sentence, self.delimiter.sep_input):
            prompt = parser.parse_line(element, token_factory)
            prompts.append(prompt)

        if auto_apply:
            self.apply(prompts)

        return prompts

    def append_pre_hook(self, func) -> None:
        self.pre_funcs.append(func)

    def append_hook(self, func: FuncConfig) -> None:
        self.funcs.append(func)


if __name__ == "__main__":
    import doctest

    doctest.testmod()
