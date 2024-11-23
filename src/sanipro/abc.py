import logging
import typing
from abc import ABC, abstractmethod
from collections.abc import MutableSequence, Sequence

logger = logging.getLogger(__name__)


class TokenInterface(ABC):
    @abstractmethod
    def __init__(self, name: str, strength: float) -> None:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def strength(self) -> float:
        pass

    @property
    @abstractmethod
    def length(self) -> int:
        pass

    @abstractmethod
    def replace(
        self, *, new_name: str | None = None, new_strength: float | None = None
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
    def get_token(
        cls,
        token_cls: type[TokenInterface],
        sentence: str,
        delimiter: str | None = None,
    ) -> typing.Generator[TokenInterface, None, None]: ...


class PromptPipelineInterface(ABC):
    def __str__(self) -> str: ...


class RunnerInterface(ABC):
    def _run_once(self) -> None: ...

    def run(self): ...


Prompt = Sequence[TokenInterface]

MutablePrompt = MutableSequence[TokenInterface]
