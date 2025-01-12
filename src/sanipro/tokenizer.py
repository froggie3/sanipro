from sanipro.abc import IPromptTokenizer, MutablePrompt, TokenInterface
from sanipro.mixins import StripLastBreakMixin, TokenizerPropertyMixins
from sanipro.parser import NormalParser


class SimpleTokenizer(IPromptTokenizer, TokenizerPropertyMixins, StripLastBreakMixin):
    def __init__(self, parser: NormalParser, token_cls: type[TokenInterface]) -> None:
        self._parser = parser
        self._token_cls = token_cls

    def tokenize_prompt(self, prompt: str) -> MutablePrompt:
        prompt = self._preprocess(prompt)
        return list(self._parser.get_token(prompt, self._token_cls))

    def _preprocess(self, prompt: str) -> str:
        """Some preprocesses for ease of implementation."""

        prompt = self._strip_last_break(prompt)
        return prompt

    @property
    def token_cls(self) -> type[TokenInterface]:
        return self._token_cls
