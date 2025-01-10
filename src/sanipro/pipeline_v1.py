from sanipro.abc import IPromptPipeline, IPromptTokenizer, MutablePrompt, TokenInterface
from sanipro.delimiter import Delimiter
from sanipro.filter_exec import IFilterExecutor
from sanipro.parser import A1111Parser as ParserV1
from sanipro.parser import NormalParser
from sanipro.pipelineresult import PipelineResult


class PromptTokenizerV1(IPromptTokenizer):
    def __init__(self, parser: NormalParser, token_cls: type[TokenInterface]) -> None:
        self._parser = parser
        self._token_cls = token_cls

    def _strip_last_break(self, prompt: str) -> str:
        """Strip last line break."""

        return prompt.strip()

    def _add_last_comma(self, prompt: str, sep: str) -> str:
        """Adds a comma to the prompt at the last."""

        if not prompt.endswith(sep):
            prompt += sep
        return prompt

    def tokenize_prompt(self, prompt: str) -> MutablePrompt:
        prompt = self._preprocess(prompt)
        return list(self._parser.get_token(prompt, self._token_cls))

    @property
    def token_cls(self) -> type[TokenInterface]:
        return self._token_cls

    def _preprocess(self, prompt: str) -> str:
        """Some preprocesses for ease of implementation."""

        delim = self._parser._delimiter.sep_input
        prompt = self._strip_last_break(prompt)
        prompt = self._add_last_comma(prompt, delim)

        return prompt


class PromptPipelineV1(IPromptPipeline):
    """Automated interface."""

    _tokens: MutablePrompt
    _tokenizer: PromptTokenizerV1
    _filter_executor: IFilterExecutor

    def __init__(
        self,
        tokenizer: PromptTokenizerV1,
        filterexecutor: IFilterExecutor,
        tokens: MutablePrompt | None = None,
    ) -> None:
        if tokens is None:
            self._tokens = []
        else:
            self._tokens = tokens

        self._tokenizer = tokenizer
        self._filter_executor = filterexecutor

    def __str__(self) -> str:
        delim = self._tokenizer._parser._delimiter.sep_output
        return delim.join(str(token) for token in self._tokens)

    def tokenize(self, source: str) -> MutablePrompt:
        return self._tokenizer.tokenize_prompt(source)

    def execute(self, prompt: str) -> PipelineResult:
        tokenized = self._tokenizer.tokenize_prompt(prompt)
        self._tokens = self._filter_executor.execute_filter_all(tokenized)
        return PipelineResult(tokenized, self._tokens)

    def new(self, prompt: MutablePrompt):
        return type(self).__init__(self, self._tokenizer, self._filter_executor, prompt)

    @property
    def tokenizer(self) -> IPromptTokenizer:
        return self._tokenizer

    @property
    def delimiter(self) -> Delimiter:
        return self._tokenizer._parser._delimiter

    @property
    def filter_executor(self) -> IFilterExecutor:
        return self._filter_executor


def create_pipeline(
    sepin: str, sepout: str, token_cls: type[TokenInterface], filt: IFilterExecutor
) -> PromptPipelineV1:
    delimiter = Delimiter(sepin, sepout)
    parser = ParserV1(delimiter=delimiter)
    tokenizer = PromptTokenizerV1(parser=parser, token_cls=token_cls)
    pipeline = PromptPipelineV1(tokenizer=tokenizer, filterexecutor=filt)

    return pipeline
