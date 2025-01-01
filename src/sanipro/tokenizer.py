
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
    def _preprocess(self, prompt: str) -> str:
        # Adding a comma in the last helps ease of implementation
        if not prompt.endswith(self.delimiter.sep_input):
            prompt += self.delimiter.sep_input
        return prompt


class PromptTokenizerV2(PromptTokenizer):
    pass
