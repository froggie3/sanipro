import logging
from abc import ABC, abstractmethod
from collections.abc import Set

from sanipro.abc import MutablePrompt, TokenInterface
from sanipro.compatible import Self

PromptSet = Set[TokenInterface]

logger = logging.getLogger(__name__)


class SetCalculator(ABC):
    """The interface for a prompt as a set of tokens,
    where it allows user to the set operation."""

    @abstractmethod
    def do_math(self, a: PromptSet, b: PromptSet) -> PromptSet: ...


class SetCalculatorWrapper:
    """The wrapper class for the specific set operation instances.
    Executes a set operation to the two prompt,
    having two prompt instances."""

    # calculator symbols
    union = "union"
    intersection = "inter"
    difference = "diff"
    symmetric_difference = "symdiff"

    def __init__(self, calcurator: SetCalculator) -> None:
        self._calcurator = calcurator

    def do_math(
        self, a: PromptSet | MutablePrompt, b: PromptSet | MutablePrompt
    ) -> PromptSet:
        return self._calcurator.do_math(set(a), set(b))

    @classmethod
    def create_from(cls, key: str | None = "union") -> Self:
        """Creates the instance from the key"""

        calculator_classes = {
            cls.union: UnionCalculator,
            cls.intersection: IntersectionCalculator,
            cls.difference: DifferenceCalculator,
            cls.symmetric_difference: SymmetricDifferenceCalculator,
        }
        try:
            calculator_cls = calculator_classes[key]
            return cls(calculator_cls())
        except KeyError:
            # TODO
            raise


class UnionCalculator(SetCalculator):
    """Calculate the union of two prompts."""

    def do_math(self, a: PromptSet, b: PromptSet) -> PromptSet:
        return a | b


class IntersectionCalculator(SetCalculator):
    """Calculate the intersection of to prompts."""

    def do_math(self, a: PromptSet, b: PromptSet) -> PromptSet:
        return a & b


class SymmetricDifferenceCalculator(SetCalculator):
    """Calculate the symmetric difference of two prompts."""

    def do_math(self, a: PromptSet, b: PromptSet) -> PromptSet:
        return a ^ b


class DifferenceCalculator(SetCalculator):
    """Calculate the difference of two prompts."""

    def do_math(self, a: PromptSet, b: PromptSet) -> PromptSet:
        return a - b
