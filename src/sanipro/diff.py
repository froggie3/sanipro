from collections.abc import Set
from functools import cached_property

from sanipro.filters.utils import collect_same_tokens
from sanipro.pipeline import MutablePrompt


class PromptDifferenceDetector:
    """Detects the difference between the two prompts."""

    def __init__(self, a: MutablePrompt, b: MutablePrompt):
        self._prompt_a = a
        self._prompt_b = b

    def get_summary(self) -> list[str]:
        """Get the summary of the difference"""
        lines = []
        lines.append(
            f"number of tokens -> {self.a} => {self.b} ({self.judged_result} {self.percentage:.2f}%)"
        )
        lines.append(f"reduced -> {self.reduced_num}")
        delimiter = ", "
        lines.append(
            f"duplicated -> {delimiter.join(self.duplicated)}"
            if self.duplicated
            else "no duplicates detected"
        )
        return lines

    @cached_property
    def duplicated(self) -> Set[str]:
        """Duplicated tokens"""
        THRESHOULD = 1
        dups = set()
        for key, tokens in collect_same_tokens(self._prompt_a).items():
            if len(tokens) > THRESHOULD:
                dups.add(key)
        return dups

    @property
    def a(self) -> int:
        """Number of tokens in prompt A"""
        return len(self._prompt_a)

    @property
    def b(self) -> int:
        """Number of tokens in prompt B"""
        return len(self._prompt_b)

    @property
    def before_num_unique(self) -> int:
        """Number of unique tokens in prompt A"""
        return len(set(self._prompt_a))

    @property
    def afrer_num_unique(self) -> int:
        """Number of unique tokens in prompt B"""
        return len(set(self._prompt_b))

    @property
    def compare(self) -> int:
        """Comparison result"""
        return 0 if self.a == self.b else -1 if self.a < self.b else 1

    @property
    def judged_result(self) -> str:
        """Judged result"""
        return (
            "equal"
            if self.compare == 0
            else "reduced" if self.compare > 0 else "increased"
        )

    @property
    def percentage(self) -> float:
        """Percentage for the difference"""
        return self.b / self.a * 100 * -1 + 100

    @property
    def reduced_num(self) -> int:
        """Difference"""
        return self.a - self.b
