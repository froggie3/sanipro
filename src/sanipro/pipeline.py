import functools
import logging
import typing
from collections.abc import Sequence

from sanipro import parser
from sanipro.abc import MutablePrompt, Prompt, PromptPipelineInterface, TokenInterface
from sanipro.delimiter import Delimiter
from sanipro.filters.abc import Command

logger = logging.getLogger(__name__)


class PromptPipeline(PromptPipelineInterface):
    __pre_funcs: list[typing.Callable[..., str]]
    __funcs: list[Command]
    __tokens: MutablePrompt
    __delimiter: Delimiter
    _parser: type[parser.ParserInterface]

    def __init__(
        self, psr: type[parser.ParserInterface], delimiter: Delimiter | None = None
    ) -> None:
        self.__pre_funcs = []
        self.__funcs = []
        self.__tokens = []
        self.__delimiter = Delimiter("", "") if delimiter is None else delimiter
        self._parser = psr

    def execute(self, prompts: Prompt, funcs: Sequence[Command] | None = None) -> None:
        """sequentially applies the filters."""
        if funcs is None:
            funcs = []
        self.append_command(*funcs)

        result = functools.reduce(lambda x, y: y.execute(x), self.__funcs, prompts)
        self.__tokens = list(result)

    def _execute_pre_hooks(self, sentence: str) -> str:
        """Executes hooks bound."""
        return functools.reduce(lambda x, y: y(x), self.__pre_funcs, sentence)

    def parse(
        self, prompt: str, token_cls: type[TokenInterface], auto_apply=False
    ) -> MutablePrompt:
        """Tokenize the prompt string."""
        prompt = self._execute_pre_hooks(prompt)
        delimiter = self.__delimiter.sep_input
        tokens = list(self._parser.get_token(token_cls, prompt, delimiter))
        # pprint.pprint(prompts, debug_fp)

        if auto_apply:
            self.execute(tokens)

        return tokens

    def append_pre_hook(self, *funcs: typing.Callable[..., str]) -> None:
        """処理前のプロンプトに対して実行されるコールバック関数を追加"""
        self.__pre_funcs.extend(funcs)

    def append_command(self, *command: Command) -> None:
        self.__funcs.extend(command)

    @property
    def delimiter(self) -> Delimiter:
        return self.__delimiter

    @property
    def tokens(self) -> MutablePrompt:
        return self.__tokens


class PromptPipelineV1(PromptPipeline):
    def __init__(
        self, psr: type[parser.ParserInterface], delimiter: Delimiter | None = None
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
