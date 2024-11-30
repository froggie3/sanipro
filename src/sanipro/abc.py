import logging
import typing
from abc import ABC, abstractmethod
from collections.abc import MutableSequence, Sequence

from sanipro.common import Delimiter

logger = logging.getLogger(__name__)


class TokenInterface(ABC):
    @abstractmethod
    def __init__(self, name: str, weight: float) -> None:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def weight(self) -> float:
        pass

    @property
    @abstractmethod
    def length(self) -> int:
        pass

    @abstractmethod
    def replace(
        self, *, new_name: str | None = None, new_weight: float | None = None
    ) -> "TokenInterface":
        pass

    @abstractmethod
    def __repr__(self) -> str:
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass


class ParserInterface(ABC):
    @classmethod
    @abstractmethod
    def get_token(
        cls,
        token_cls: type[TokenInterface],
        sentence: str,
        delimiter: str | None = None,
    ) -> typing.Generator[TokenInterface, None, None]: ...


class PromptPipelineInterface(ABC):
    @abstractmethod
    def __init__(
        self, psr: type[ParserInterface], delimiter: Delimiter | None = None
    ): ...

    @abstractmethod
    def __str__(self) -> str: ...


Prompt = Sequence[TokenInterface]

MutablePrompt = MutableSequence[TokenInterface]
