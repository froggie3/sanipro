import functools
import logging
import typing
from collections.abc import Sequence

from . import filters, parser
from .abc import MutablePrompt, Prompt, TokenInterface

logger = logging.getLogger(__name__)


class Delimiter(typing.NamedTuple):
    sep_input: str
    sep_output: str

    def create_pipeline(
        self,
        cls: type["PromptPipeline"],
    ) -> "PromptPipeline":
        """Creates pipeline from Delimiter object"""
        pipeline = None
        if cls is PromptPipelineV1:
            pipeline = cls(
                parser.ParserV1,
                self,
            )
        elif cls is PromptPipelineV2:
            pipeline = cls(
                parser.ParserV2,
                self,
            )
        if pipeline is not None:
            return pipeline

        raise NotImplementedError


class PromptPipeline:
    pre_funcs: list[typing.Callable[..., str]]
    funcs: list[filters.Command]
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

    def execute(
        self,
        prompts: Prompt,
        funcs: Sequence[filters.Command] | None = None,
    ) -> None:
        """sequentially applies the filters."""
        if funcs is None:
            funcs = []
        self.append_command(*funcs)

        result = functools.reduce(
            lambda x, y: y.execute(x),
            self.funcs,
            prompts,
        )
        self.tokens = list(result)

    def _execute_pre_hooks(self, sentence: str) -> str:
        """Executes hooks bound."""
        return functools.reduce(lambda x, y: y(x), self.pre_funcs, sentence)

    def parse(
        self,
        prompt: str,
        token_cls: type[TokenInterface],
        auto_apply=False,
    ) -> MutablePrompt:
        """Tokenize the prompt string."""
        prompt = self._execute_pre_hooks(prompt)

        delimiter = self.delimiter.sep_input

        tokens = list(self._parser.get_token(token_cls, prompt, delimiter))

        # pprint.pprint(prompts, debug_fp)

        if auto_apply:
            self.execute(tokens)

        return tokens

    def append_pre_hook(self, *funcs: typing.Callable[..., str]) -> None:
        """処理前のプロンプトに対して実行されるコールバック関数を追加"""
        self.pre_funcs.extend(funcs)

    def append_command(self, *command: filters.Command) -> None:
        self.funcs.extend(command)


class PromptPipelineV1(PromptPipeline):
    def __init__(
        self,
        psr: type[parser.Parser],
        delimiter: Delimiter | None = None,
    ) -> None:
        PromptPipeline.__init__(self, psr, delimiter)

        def add_last_comma(sentence: str) -> str:
            if not sentence.endswith(self.delimiter.sep_input):
                sentence += self.delimiter.sep_input
            return sentence

        self.append_pre_hook(add_last_comma)

    def __str__(self) -> str:
        delim = self.delimiter.sep_output
        lines = map(lambda token: str(token), self.tokens)

        return delim.join(lines)


class PromptPipelineV2(PromptPipeline):
    def __str__(self) -> str:
        delim = ""
        lines = map(lambda token: str(token), self.tokens)
        return delim.join(lines)


if __name__ == "__main__":
    import doctest

    doctest.testmod()
