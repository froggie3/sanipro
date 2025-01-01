from sanipro.abc import IPromptPipeline, IPromptTokenizer, MutablePrompt, TokenInterface
from sanipro.delimiter import Delimiter
from sanipro.filter_exec import IFilterExecutor
from sanipro.logger import logger


class PromptPipeline(IPromptPipeline):
    """Automated interface."""

    _tokens: MutablePrompt
    _tokenizer: IPromptTokenizer
    _filter_executor: IFilterExecutor

    def __init__(
        self, tokenizer: IPromptTokenizer, filterexecutor: IFilterExecutor
    ) -> None:
        self._tokens = []
        self._tokenizer = tokenizer
        self._filter_executor = filterexecutor
        logger.debug(f"{type(self).__name__} initialized.")

    def tokenize(self, source: str) -> MutablePrompt:
        return self._tokenizer.tokenize_prompt(source)

    def execute(self, prompt: str) -> MutablePrompt:
        tokenized = self._tokenizer.tokenize_prompt(prompt)
        self._tokens = self._filter_executor.execute_filter_all(tokenized)
        return self._tokens

    def reset(self) -> None:
        self._tokens.clear()
        self._filter_executor.clear_commands()

    def get_state(self) -> dict:
        return {
            "tokens": self._tokens,
            "filters": self._filter_executor.get_commands(),
            "delimiter": self._tokenizer.delimiter,
        }

    def update_delimiter(self, delimiter: Delimiter) -> None:
        self._tokenizer.delimiter = delimiter

    def update_tokenizer(self, tokenizer: IPromptTokenizer) -> None:
        self._tokenizer = tokenizer

    @property
    def token_cls(self) -> type[TokenInterface]:
        return self._tokenizer.token_cls

    @property
    def tokens(self) -> MutablePrompt:
        return self._tokens

    @property
    def delimiter(self) -> Delimiter:
        return self._tokenizer.delimiter

    @property
    def tokenizer(self) -> IPromptTokenizer:
        return self._tokenizer

    @property
    def filter_executor(self) -> IFilterExecutor:
        return self._filter_executor


class PromptPipelineV1(PromptPipeline):
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
