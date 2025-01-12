from sanipro.abc import (
    DelimiterGetterMixin,
    IPromptPipelineSelializableMixin,
    IPromptTokenizer,
    ParserGetterMixin,
    ParserInterface,
    TokenClassGetterMixin,
    TokenInterface,
    TokenizerGetterMixin,
)
from sanipro.delimiter import Delimiter
from sanipro.filter_exec import IFilterExecutor


class TokenizerPropertyMixins(
    ParserGetterMixin, DelimiterGetterMixin, TokenClassGetterMixin
):
    _token_cls: type[TokenInterface]
    _parser: ParserInterface

    @property
    def token_cls(self) -> type[TokenInterface]:
        return self._token_cls

    @property
    def parser(self) -> ParserInterface:
        return self._parser

    @property
    def delimiter(self) -> Delimiter:
        return self._parser.delimiter


class PromptPipelinePropertyMixins(
    IPromptPipelineSelializableMixin, TokenizerGetterMixin, DelimiterGetterMixin
):
    _tokenizer: IPromptTokenizer
    _filter_executor: IFilterExecutor

    @property
    def tokenizer(self) -> IPromptTokenizer:
        return self._tokenizer

    @property
    def delimiter(self) -> Delimiter:
        return self._tokenizer.parser.delimiter

    @property
    def filter_executor(self) -> IFilterExecutor:
        return self._filter_executor


class ParserPropertyMixins(DelimiterGetterMixin):
    _delimiter: Delimiter

    @property
    def delimiter(self) -> Delimiter:
        return self._delimiter


class StripLastBreakMixin:
    def _strip_last_break(self, prompt: str) -> str:
        """Strip last line break."""
        return prompt.strip()
