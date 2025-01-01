import re

from sanipro.abc import IPromptTokenizer, MutablePrompt, TokenInterface
from sanipro.delimiter import Delimiter
from sanipro.parser import ParserInterface


class PromptTokenizer(IPromptTokenizer):
    """Tokenize the prompt string using the parser."""

    _delimiter: Delimiter
    _parser: type[ParserInterface]

    def __init__(
        self,
        psr: type[ParserInterface],
        token_cls: type[TokenInterface],
        delimiter: Delimiter,
    ) -> None:
        self._parser = psr
        self._token_cls = token_cls
        self._delimiter = delimiter

    def _preprocess(self, prompt: str) -> str:
        """Allow the subclasses to preprocess the prompt."""
        return prompt

    def tokenize_prompt(self, prompt: str) -> MutablePrompt:
        prompt = self._preprocess(prompt)

        return list(
            self._parser.get_token(self._token_cls, prompt, self._delimiter.sep_input)
        )

    @property
    def token_cls(self) -> type[TokenInterface]:
        return self._token_cls

    @property
    def delimiter(self) -> Delimiter:
        return self._delimiter

    @delimiter.setter
    def delimiter(self, value: Delimiter) -> None:
        self._delimiter = value

    @property
    def parser(self) -> type[ParserInterface]:
        return self._parser

    def update_parser(self, psr: type[ParserInterface]) -> None:
        self._parser = psr


class PromptTokenizerV1(PromptTokenizer):

    def _strip_last_break(self, prompt: str) -> str:
        """Strip last line break."""

        return prompt.strip()

    def _escape_colons(self, prompt: str) -> str:
        """Escape colons."""

        sep = self.delimiter.sep_input
        re_pattern = re.compile(r":(?!\d+(?:\.\d+)?)")
        return sep.join(re.sub(re_pattern, "\:", token) for token in prompt.split(sep))

    def _add_last_comma(self, prompt: str) -> str:
        """Adds a comma to the prompt at the last."""

        sep = self.delimiter.sep_input
        if not prompt.endswith(sep):
            prompt += sep
        return prompt

    def _preprocess(self, prompt: str) -> str:
        """Some preprocesses for ease of implementation."""

        prompt = self._strip_last_break(prompt)
        prompt = self._escape_colons(prompt)
        prompt = self._add_last_comma(prompt)

        return prompt


class PromptTokenizerV2(PromptTokenizer):
    pass
