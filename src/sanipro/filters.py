import collections
import logging
import random
import typing
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from functools import partial
from itertools import chain

from sanipro import fuzzysort

from . import sort_all_factory, utils
from .abc import MutablePrompt, Prompt, TokenInterface

logger = logging.getLogger(__name__)


class Command(ABC):
    @abstractmethod
    def execute(self, prompt: Prompt) -> MutablePrompt: ...


def collect_same_tokens(prompts: Prompt) -> Mapping[str, MutablePrompt]:
    groups = collections.defaultdict(list)
    for prompt in prompts:
        groups[prompt.name].append(prompt)
    return groups


def collect_same_tokens_sorted(
    prompt: Prompt, reverse=False
) -> typing.Generator[list[TokenInterface], None, None]:
    f = sort_all_factory.sort_by_strength
    return (
        sorted(token, key=f, reverse=reverse)
        for token in collect_same_tokens(prompt).values()
    )


class MaskCommand(Command):
    def __init__(self, excludes: Sequence[str], replace_to: str):
        self.excludes = excludes
        self.replace_to = replace_to

    def execute(self, prompt: Prompt) -> MutablePrompt:
        """
        >>> from lib.common import PromptInteractive
        >>> p = mask([PromptInteractive('white hair', 1.2), PromptInteractive('thighhighs', 1.0)], ['white'])
        >>> [x.name for x in p]
        ['%%%', 'thighhighs']
        """
        return [
            token.replace(self.replace_to) if token.name in self.excludes else token
            for token in prompt
        ]


class ExcludeCommand(Command):
    def __init__(self, excludes: Sequence[str]):
        self.excludes = excludes

    def execute(self, prompt: Prompt) -> MutablePrompt:
        """
        >>> from lib.common import PromptInteractive
        >>> p = exclude([PromptInteractive('white hair', 1.2), PromptInteractive('thighhighs', 1.0)], ['white'])
        >>> [x.name for x in p]
        ['thighhighs']
        """
        return [token for token in prompt if token.name not in self.excludes]


class SortAllCommand(Command):
    def __init__(self, sorted_partial: partial, reverse: bool = False):
        self.sorted_partial = sorted_partial
        self.reverse = reverse

    def execute(self, prompt: Prompt) -> MutablePrompt:
        return self.sorted_partial(prompt, reverse=self.reverse)


class RoundUpCommand(Command):
    def __init__(self, digits: int):
        self.digits = digits

    def execute(self, prompt: Prompt) -> MutablePrompt:
        return [utils.round_token_weight(token, self.digits) for token in prompt]


class RandomCommand(Command):
    def __init__(self, seed: int | None = None):
        self.seed = seed

    def execute(self, prompt: Prompt) -> MutablePrompt:
        if self.seed is not None:
            random.seed(self.seed)

        if not isinstance(prompt, typing.MutableSequence):
            _prompt = random.sample(prompt, len(prompt))
            return _prompt

        random.shuffle(prompt)
        return prompt


class SortCommand(Command):
    def __init__(self, reverse: bool = False):
        self.reverse = reverse

    def execute(self, prompt: Prompt) -> MutablePrompt:
        """
        >>> from lib.common import PromptInteractive
        >>> p = sort([PromptInteractive('white hair', 1.2), PromptInteractive('white hair', 1.0)])
        >>> [(x.name, x.strength) for x in p]
        [('white hair', 1.0), ('white hair', 1.2)]

        >>> from lib.common import PromptInteractive
        >>> p = sort([PromptInteractive('white hair', 1.2), PromptInteractive('white hair', 1.0)], True)
        >>> [(x.name, x.strength) for x in p]
        [('white hair', 1.2), ('white hair', 1.0)]
        """
        return list(chain(*collect_same_tokens_sorted(prompt, self.reverse)))


class SimilarCommand(Command):
    def __init__(self, reorderer: fuzzysort.ReordererStrategy):
        self.reorderer = reorderer

    def execute(self, prompt: Prompt) -> MutablePrompt:
        sorted_words_seq = self.reorderer.find_optimal_order(prompt)
        return sorted_words_seq


class UniqueCommand(Command):
    def __init__(self, reverse: bool = False):
        self.reverse = reverse

    def execute(self, prompt: Prompt) -> MutablePrompt:
        """
        >>> from lib.common import PromptInteractive
        >>> p = unique([PromptInteractive('white hair', 1.2), PromptInteractive('white hair', 1.0)])
        >>> [(x.name, x.strength) for x in p]
        [('white hair', 1.0)]

        >>> from lib.common import PromptInteractive
        >>> p = unique([PromptInteractive('white hair', 1.2), PromptInteractive('white hair', 1.0)], True)
        >>> [(x.name, x.strength) for x in p]
        [('white hair', 1.2)]
        """
        return [vals[0] for vals in collect_same_tokens_sorted(prompt, self.reverse)]


if __name__ == "__main__":
    import doctest

    doctest.testmod()
