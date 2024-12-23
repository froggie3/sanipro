import logging
import typing
from abc import ABC, abstractmethod
from collections.abc import MutableSequence, Sequence

from sanipro.compatible import Self
from sanipro.delimiter import Delimiter

logger = logging.getLogger(__name__)


class TokenInterface(ABC):
    """Interface for the token."""

    @abstractmethod
    def __init__(self, name: str, weight: float) -> None:
        pass

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def weight(self) -> float: ...

    @property
    @abstractmethod
    def length(self) -> int: ...

    @abstractmethod
    def replace(
        self, *, new_name: str | None = None, new_weight: float | None = None
    ) -> Self: ...

    @abstractmethod
    def __repr__(self) -> str: ...

    @abstractmethod
    def __str__(self) -> str: ...


class ParserInterface(ABC):
    """Interface for the parser."""

    @classmethod
    @abstractmethod
    def get_token(
        cls,
        token_cls: type[TokenInterface],
        sentence: str,
        delimiter: str | None = None,
    ) -> typing.Generator[TokenInterface, None, None]:
        """Get the token from the sentence."""


Prompt = Sequence[TokenInterface]

MutablePrompt = MutableSequence[TokenInterface]


class IPromptTokenizer(ABC):
    """Interface for the prompt tokenizer."""

    @abstractmethod
    def tokenize_prompt(self, prompt: str) -> MutablePrompt:
        """Tokenize the prompt string using the parser."""

    @property
    def token_cls(self) -> type[TokenInterface]: ...

    @property
    @abstractmethod
    def delimiter(self) -> Delimiter: ...

    @delimiter.setter
    @abstractmethod
    def delimiter(self, value: Delimiter) -> None: ...


class IPromptPipeline(ABC):
    """Interface for the prompt pipeline."""

    @abstractmethod
    def execute(self, prompt: str) -> MutablePrompt:
        """Tokenize the prompt string using the parser interface."""

    @abstractmethod
    def __str__(self) -> str:
        """Stringify the pipeline."""
        ...
