from sanipro.abc import IPromptTokenizer, MutablePrompt, TokenInterface
from sanipro.mixins import TokenizerPropertyMixins
from sanipro.parser import NormalParser


class SimpleTokenizer(IPromptTokenizer, TokenizerPropertyMixins):
    def __init__(self, parser: NormalParser, token_cls: type[TokenInterface]) -> None:
        self._parser = parser
        self._token_cls = token_cls

    def tokenize_prompt(self, prompt: str) -> MutablePrompt:
        return list(self._parser.get_token(prompt, self._token_cls))

    @property
    def token_cls(self) -> type[TokenInterface]:
        return self._token_cls
