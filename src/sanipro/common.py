import functools
import logging
import typing
from collections.abc import Sequence

from . import filters, parser
from .abc import MutablePrompt, Prompt, TokenInterface

logger = logging.getLogger(__name__)


class FuncConfig(typing.NamedTuple):
    func: filters.Filters
    kwargs: Sequence[tuple[str, typing.Any]] | dict[str, typing.Any]


class Delimiter(typing.NamedTuple):
    sep_input: str
    sep_output: str

    def create_builder(
        self,
        cls: type["PromptBuilder"],
    ) -> "PromptBuilder":

        builder = None
        if cls is PromptBuilderV1:
            builder = cls(
                parser.ParserV1,
                self,
            )
        elif cls is PromptBuilderV2:
            builder = cls(
                parser.ParserV2,
                self,
            )
        if builder is not None:
            return builder

        raise NotImplementedError


class PromptBuilder:
    pre_funcs: list[typing.Callable[..., str]]
    funcs: list[FuncConfig]
    tokens: MutablePrompt
    delimiter: Delimiter
    _parser: type[parser.Parser]

    def __init__(
        self,
        psr: type[parser.Parser],
        delimiter: Delimiter | None = None,
    ) -> None:
        self.pre_funcs = []
        self.funcs = []
        self.tokens = []
        self.delimiter = Delimiter("", "") if delimiter is None else delimiter
        self._parser = psr

    def __str__(self) -> str:
        raise NotImplementedError

    def apply(
        self,
        prompts: Prompt,
        funcs: Sequence[FuncConfig] | None = None,
    ) -> None:
        """sequentially applies the filters."""
        if funcs is None:
            funcs = []
        self.append_hook(*funcs)

        result = functools.reduce(
            lambda x, y: y.func(x, **dict(y.kwargs)),
            self.funcs,
            prompts,
        )
        self.tokens = list(result)

    def _execute_pre_hooks(self, sentence: str) -> str:
        """executes hooks bound"""
        return functools.reduce(lambda x, y: y(x), self.pre_funcs, sentence)

    def parse(
        self,
        sentence: str,
        token_cls: type[TokenInterface],
        auto_apply=False,
    ) -> MutablePrompt:
        sentence = self._execute_pre_hooks(sentence)

        delimiter = self.delimiter.sep_input

        prompts = list(self._parser.get_token(token_cls, sentence, delimiter))

        # pprint.pprint(prompts, debug_fp)

        if auto_apply:
            self.apply(prompts)

        return prompts

    def append_pre_hook(self, *funcs: typing.Callable[..., str]) -> None:
        """処理前のプロンプトに対して実行されるコールバック関数を追加"""
        self.pre_funcs.extend(funcs)

    def append_hook(self, *funcs: FuncConfig) -> None:
        self.funcs.extend(funcs)


class PromptBuilderV1(PromptBuilder):
    def __init__(
        self,
        psr: type[parser.Parser],
        delimiter: Delimiter | None = None,
    ) -> None:
        PromptBuilder.__init__(self, psr, delimiter)

        def add_last_comma(sentence: str) -> str:
            if not sentence.endswith(self.delimiter.sep_input):
                sentence += self.delimiter.sep_input
            return sentence

        self.append_pre_hook(add_last_comma)

    def __str__(self) -> str:
        delim = self.delimiter.sep_output
        lines = map(lambda token: str(token), self.tokens)

        return delim.join(lines)


class PromptBuilderV2(PromptBuilder):
    def __str__(self) -> str:
        delim = ""
        lines = map(lambda token: str(token), self.tokens)
        return delim.join(lines)


if __name__ == "__main__":
    import doctest

    doctest.testmod()
