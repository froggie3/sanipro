import logging
from pprint import pprint
from typing import Any, Callable, NamedTuple, Type

from . import parser, utils
from .abc import TokenInterface

logger = logging.getLogger()

debug_fp = utils.BufferingLoggerWriter(logger, logging.DEBUG)


class FuncConfig(NamedTuple):
    # func: Callable[...]
    func: Callable
    kwargs: tuple[tuple[str, Any], ...]


class Delimiter(NamedTuple):
    sep_input: str
    sep_output: str

    @classmethod
    def create_builder(
        cls, input: str, output: str, parser: type[parser.Parser] = parser.ParserV1
    ) -> "PromptBuilder":
        builder = PromptBuilder(
            parser,
            cls(input, output),
        )

        return builder


class PromptBuilder:
    def __init__(
        self,
        psr: type[parser.Parser],
        delimiter: Delimiter | None = None,
    ):
        self.pre_funcs = []
        self.funcs: list[FuncConfig] = []
        self.tokens = []
        self.delimiter = delimiter
        self.parser: type[parser.Parser] = psr

    def __str__(self) -> str:
        lines = []
        delim = ""
        if self.delimiter is not None:
            delim = getattr(self.delimiter, "sep_output")

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

    def _execute_pre_hooks(self, sentence: str) -> str:
        """executes hooks bound"""
        for hook in self.pre_funcs:
            sentence = hook(sentence)
        return sentence

    def parse(
        self, sentence: str, token_factory: Type[TokenInterface], auto_apply=False
    ) -> list[TokenInterface]:
        prompts = []
        sentence = self._execute_pre_hooks(sentence)

        delimiter = ""
        if self.delimiter is not None:
            delimiter = getattr(self.delimiter, "sep_input")

        for element in self.parser.get_token(token_factory, sentence, delimiter):
            prompts.append(element)

        pprint(prompts, debug_fp)
        if auto_apply:
            self.apply(prompts)
        return prompts

    def append_pre_hook(self, func) -> None:
        """処理前のプロンプトに対して実行されるコールバック関数を追加"""
        self.pre_funcs.append(func)

    def append_hook(self, func: FuncConfig) -> None:
        self.funcs.append(func)


if __name__ == "__main__":
    import doctest

    doctest.testmod()
