from abc import ABC, abstractmethod
from collections.abc import Set

from sanipro.abc import Prompt, TokenInterface

PromptSet = Set[TokenInterface]


class SetCalculator(ABC):
    """The interface for a prompt as a set of tokens,
    where it allows user to the set operation."""

    @abstractmethod
    def do_math(self, a: Prompt, b: Prompt) -> Prompt:
        """Do the set operation."""


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

    def __init__(self, reverse=False) -> None:
        self.reverse = reverse

    def do_math(self, a: Prompt, b: Prompt) -> Prompt:
        if not self.reverse:
            return tuple(set(a) - set(b))
        return tuple(set(b) - set(a))
