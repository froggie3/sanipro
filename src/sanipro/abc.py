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
    def name(self) -> str:
        """Token."""

    @property
    @abstractmethod
    def weight(self) -> float:
        """Weight."""

    @property
    @abstractmethod
    def length(self) -> int:
        """The length of the token."""

    @abstractmethod
    def replace(
        self, *, new_name: str | None = None, new_weight: float | None = None
    ) -> Self:
        """Replace a specific property of the token."""

    @abstractmethod
    def __repr__(self) -> str: ...


Prompt = Sequence[TokenInterface]

MutablePrompt = MutableSequence[TokenInterface]


class TokenGettableMixin(ABC):
    @abstractmethod
    def get_token(
        self, sentence: str, token_cls: type[TokenInterface]
    ) -> typing.Generator[TokenInterface, None, None]:
        """Get the token from the sentence."""


class DelimiterGetterMixin(ABC):
    @property
    @abstractmethod
    def delimiter(self) -> "Delimiter":
        """Get delimiter."""


class ParserInterface(TokenGettableMixin, DelimiterGetterMixin, ABC):
    """Interface for the parser."""


class TokenClassGetterMixin(ABC):
    @property
    @abstractmethod
    def token_cls(self) -> type[TokenInterface]:
        """Get token class."""


class ParserGetterMixin(ABC):
    @property
    @abstractmethod
    def parser(self) -> ParserInterface:
        """Get parser."""


class IPromptTokenizerTokenizableMixin(ABC):
    @abstractmethod
    def tokenize_prompt(self, prompt: str) -> MutablePrompt:
        """Tokenize the prompt string using the parser."""


class IPromptTokenizer(
    IPromptTokenizerTokenizableMixin,
    ParserGetterMixin,
    DelimiterGetterMixin,
    TokenClassGetterMixin,
    ABC,
):
    """Interface for the prompt tokenizer."""

    @abstractmethod
    def __init__(
        self, parser: ParserInterface, token_cls: type[TokenInterface]
    ) -> None: ...


class IPipelineResult(ABC):
    """Interface for the result."""

    @abstractmethod
    def get_summary(self) -> list[str]:
        """Get the result of the pipeline."""


class IPromptPipelineExecutableMixin(ABC):
    @abstractmethod
    def execute(self, prompt: str) -> IPipelineResult:
        """Tokenize the prompt string using the parser interface."""


class IPromptPipelineSelializableMixin(ABC):
    @abstractmethod
    def __str__(self) -> str:
        """Stringify the pipeline."""


class TokenizerGetterMixin(ABC):
    @property
    @abstractmethod
    def tokenizer(self) -> IPromptTokenizer:
        """Get tokenizer."""


class IPromptPipelineDelimiterNewableMixin(ABC):
    @abstractmethod
    def new(self, prompt: MutablePrompt):
        """Creates a new instance of the pipeline, importing new prompt."""


class IPromptPipeline(
    IPromptPipelineExecutableMixin,
    IPromptPipelineDelimiterNewableMixin,
    IPromptPipelineSelializableMixin,
    TokenizerGetterMixin,
    DelimiterGetterMixin,
):
    """PromptPipeline interface."""
