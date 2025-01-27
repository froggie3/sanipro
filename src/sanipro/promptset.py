from abc import ABC, abstractmethod
from collections.abc import Set

from sanipro.abc import Prompt, TokenInterface
from sanipro.compatible import Self

PromptSet = Set[TokenInterface]


class SetCalculator(ABC):
    """The interface for a prompt as a set of tokens,
    where it allows user to the set operation."""

    @abstractmethod
    def do_math(self, a: Prompt, b: Prompt) -> Prompt:
        """Do the set operation."""


class SetCalculatorWrapper:
    """The wrapper class for the specific set operation instances.
    Executes a set operation to the two prompt,
    having two prompt instances."""

    def __init__(self, calcurator: SetCalculator) -> None:
        self._calcurator = calcurator

    def do_math(self, a: Prompt, b: Prompt) -> Prompt:
        return self._calcurator.do_math(a, b)

    @classmethod
    def create_from(cls, key: str | None = "union") -> Self:
        """Creates the instance from the key"""

        if key == "union":
            return cls(UnionCalculator())
        elif key == "inter":
            return cls(IntersectionCalculator())
        elif key == "diff":
            return cls(DifferenceCalculator())
        elif key == "symdiff":
            return cls(SymmetricDifferenceCalculator())

        return cls(UnionCalculator())


class UnionCalculator(SetCalculator):
    """Calculate the union of two prompts."""

    def do_math(self, a: Prompt, b: Prompt) -> Prompt:
        return tuple(set(a) | set(b))


class IntersectionCalculator(SetCalculator):
    """Calculate the intersection of to prompts."""

    def do_math(self, a: Prompt, b: Prompt) -> Prompt:
        return tuple(set(a) & set(b))


class SymmetricDifferenceCalculator(SetCalculator):
    """Calculate the symmetric difference of two prompts."""

    def do_math(self, a: Prompt, b: Prompt) -> Prompt:
        return tuple(set(a) ^ set(b))


class DifferenceCalculator(SetCalculator):
    """Calculate the difference of two prompts."""

    def do_math(self, a: Prompt, b: Prompt, reverse=False) -> Prompt:
        if not reverse:
            return tuple(set(a) - set(b))
        return tuple(set(b) - set(a))
