from collections.abc import Callable

from sanipro.abc import IPromptPipeline, IPromptTokenizer, MutablePrompt, TokenInterface
from sanipro.delimiter import Delimiter
from sanipro.filter_exec import IFilterExecutor
from sanipro.mixins import (
    PromptPipelinePropertyMixins,
    StripLastBreakMixin,
    TokenizerPropertyMixins,
)
from sanipro.parser import NormalParser
from sanipro.parser_a1111 import A1111ParserUngrouped
from sanipro.pipelineresult import PipelineResult


class A1111Tokenizer(IPromptTokenizer, TokenizerPropertyMixins, StripLastBreakMixin):
    def __init__(self, parser: NormalParser, token_cls: type[TokenInterface]) -> None:
        self._parser = parser
        self._token_cls = token_cls

    def _add_last_comma(self, prompt: str, sep: str) -> str:
        """Adds a comma to the prompt at the last."""

        if not prompt.endswith(sep):
            prompt += sep
        return prompt

    def tokenize_prompt(self, prompt: str) -> MutablePrompt:
        prompt = self._preprocess(prompt)
        return list(self._parser.get_token(prompt, self._token_cls))

    def _preprocess(self, prompt: str) -> str:
        """Some preprocesses for ease of implementation."""

        delim = self._parser.delimiter.sep_input
        prompt = self._strip_last_break(prompt)
        prompt = self._add_last_comma(prompt, delim)

        return prompt


class PromptPipelineV1(IPromptPipeline, PromptPipelinePropertyMixins):
    """Automated interface."""

    def __init__(
        self,
        tokenizer: IPromptTokenizer,
        filter_executor: IFilterExecutor,
        token_formatter: Callable,
        tokens: MutablePrompt | None = None,
    ) -> None:
        self._tokens: MutablePrompt
        if tokens is None:
            self._tokens = []
        else:
            self._tokens = tokens

        self._tokenizer = tokenizer
        self._filter_executor = filter_executor
        self._token_formatter = token_formatter

    def __str__(self) -> str:
        delim = self._tokenizer.parser.delimiter.sep_output
        formatter = self._token_formatter
        return delim.join(formatter(token) for token in self._tokens)

    def tokenize(self, source: str) -> MutablePrompt:
        return self._tokenizer.tokenize_prompt(source)

    def execute(self, prompt: str) -> PipelineResult:
        tokenized = self._tokenizer.tokenize_prompt(prompt)
        self._tokens = self._filter_executor.execute_filter_all(tokenized)
        return PipelineResult(tokenized, self._tokens)

    def new(self, prompt: MutablePrompt):
        return type(self).__init__(
            self, self._tokenizer, self._filter_executor, self._token_formatter, prompt
        )


def create_pipeline(
    sepin: str,
    sepout: str,
    token_cls: type[TokenInterface],
    filt: IFilterExecutor,
    token_formatter: Callable,
) -> PromptPipelineV1:
    """Handy funtion to create a pipeline."""

    delimiter = Delimiter(sepin, sepout)
    parser = A1111ParserUngrouped(delimiter=delimiter)
    tokenizer = A1111Tokenizer(parser=parser, token_cls=token_cls)
    pipeline = PromptPipelineV1(
        tokenizer=tokenizer, filter_executor=filt, token_formatter=token_formatter
    )

    return pipeline
