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
        lines = []
        delim = getattr(self.delimiter, "sep_output") if self.has_delimiter() else ""

        for token in self.tokens:
            lines.append(str(token))

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
    ) -> "PromptBuilder":
        """sequentially applies the filters."""
        if funcs is None:
            funcs = []

        for func in funcs:
            self.append_hook(func)

        for func in self.funcs:
            prompts = func.func(
                prompts,
                **dict(func.kwargs),
            )
            func_name = func.func.__name__
            logger.debug(f"the hook {func_name!r} executed")

        self.tokens = list(prompts)
        return self

    def _execute_pre_hooks(self, sentence: str) -> str:
        """executes hooks bound"""
        for func in self.pre_funcs:
            sentence = func(sentence)
        return sentence

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

        prompts = list(self._parser.get_token(
            token_cls,
            sentence,
            delimiter,
        ))

        pprint.pprint(prompts, debug_fp)

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
