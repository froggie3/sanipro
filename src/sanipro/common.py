import functools
import logging
import pprint
import typing
from collections.abc import Sequence

from . import parser
from .abc import TokenInterface
from .utils import debug_fp

logger = logging.getLogger(__name__)


class FuncType(typing.Protocol):
    def __call__(
        self,
        prompts: Sequence[TokenInterface],
        *args: typing.Any,
        **kwargs: typing.Any,
    ) -> Sequence[TokenInterface]: ...

    @property
    def __name__(self) -> str: ...


class FuncConfig(typing.NamedTuple):
    func: FuncType
    kwargs: tuple[tuple[str, typing.Any], ...]


class Delimiter(typing.NamedTuple):
    sep_input: str
    sep_output: str

    @classmethod
    def create_builder(
        cls,
        input: str,
        output: str,
        parser: type[parser.Parser] = parser.ParserV1,
    ) -> "PromptBuilder":
        builder = PromptBuilder(
            parser,
            cls(input, output),
        )

        return builder


class PromptBuilder:
    pre_funcs: list[typing.Callable[..., str]]
    funcs: list[FuncConfig]
    tokens: list[TokenInterface]
    delimiter: Delimiter | None
    _parser: type[parser.Parser]

    def __init__(
        self,
        psr: type[parser.Parser],
        delimiter: Delimiter | None = None,
    ):
        self.pre_funcs = []
        self.funcs = []
        self.tokens = []
        self.delimiter = delimiter
        self._parser = psr

    def has_delimiter(self):
        return self.delimiter is not None

    def __str__(self) -> str:
        delim = getattr(self.delimiter, "sep_output") if self.has_delimiter() else ""
        lines = map(lambda token: str(token), self.tokens)

        return delim.join(lines)

    def map_token(
        self,
        attr: str,
        func: typing.Callable,
    ) -> None:
        for token in self.tokens:
            val = getattr(token, attr)
            val = func(val)
            setattr(token, attr, val)

    def apply(
        self,
        prompts: Sequence[TokenInterface],
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
    ) -> list[TokenInterface]:
        sentence = self._execute_pre_hooks(sentence)

        delimiter = ""
        if self.delimiter is not None:
            delimiter = getattr(self.delimiter, "sep_input")

        prompts = list(self._parser.get_token(token_cls, sentence, delimiter))
        pprint.pprint(prompts, debug_fp)

        if auto_apply:
            self.apply(prompts)

        return prompts

    def append_pre_hook(self, *funcs: typing.Callable) -> None:
        """処理前のプロンプトに対して実行されるコールバック関数を追加"""
        self.pre_funcs.extend(funcs)

    def append_hook(self, *funcs: FuncConfig) -> None:
        self.funcs.extend(funcs)


if __name__ == "__main__":
    import doctest

    doctest.testmod()
