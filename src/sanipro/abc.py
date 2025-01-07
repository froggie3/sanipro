import typing
from abc import ABC, abstractmethod
from collections.abc import MutableSequence, Sequence

from sanipro.compatible import Self

if typing.TYPE_CHECKING:
    from sanipro.delimiter import Delimiter


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

    @abstractmethod
    def get_token(
        self, sentence: str, token_cls: type[TokenInterface]
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


class IPipelineResult(ABC):
    """Interface for the result."""

    @abstractmethod
    def get_summary(self) -> list[str]: ...


class IPromptPipelineExecutable(ABC):
    @abstractmethod
    def execute(self, prompt: str) -> IPipelineResult:
        """Tokenize the prompt string using the parser interface."""


class IPromptPipelineSelializable(ABC):
    @abstractmethod
    def __str__(self) -> str:
        """Stringify the pipeline."""
        ...


class IPromptPipelineTokenizerGetter(ABC):
    @property
    @abstractmethod
    def tokenizer(self) -> IPromptTokenizer: ...


class IPromptPipelineDelimiterGetter(ABC):
    @property
    @abstractmethod
    def delimiter(self) -> "Delimiter": ...


class IPromptPipelineDelimiterNewable(ABC):
    @abstractmethod
    def new(self, prompt: MutablePrompt): ...


class IPromptPipeline(
    IPromptPipelineExecutable,
    IPromptPipelineSelializable,
    IPromptPipelineTokenizerGetter,
    IPromptPipelineDelimiterGetter,
    IPromptPipelineDelimiterNewable,
):
    pass
