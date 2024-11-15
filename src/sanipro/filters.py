import collections
import functools
import itertools
import logging
import random
import typing
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence

from . import sort_all_factory
from .abc import MutablePrompt, Prompt, TokenInterface

logger = logging.getLogger(__name__)


class Command(ABC):
    @abstractmethod
    def execute(
        self,
        prompt: Prompt,
    ) -> MutablePrompt:
        raise NotImplementedError


def collect_same_tokens(
    prompts: Prompt,
) -> Mapping[str, MutablePrompt]:
    groups = collections.defaultdict(list)
    for prompt in prompts:
        groups[prompt.name].append(prompt)
    return groups


def collect_same_tokens_sorted(
    prompt: Prompt,
    reverse=False,
) -> typing.Generator[list[TokenInterface], None, None]:
    f = sort_all_factory.sort_by_strength
    return (
        sorted(tokens, key=f, reverse=reverse)
        for tokens in collect_same_tokens(prompt).values()
    )


class MaskCommand(Command):
    def __init__(
        self,
        excludes: Sequence[str],
        replace_to: str,
    ):
        self.excludes = excludes
        self.replace_to = replace_to

    def execute(
        self,
        prompt: Prompt,
    ) -> MutablePrompt:
        """
        >>> from lib.common import PromptInteractive
        >>> p = mask([PromptInteractive('white hair', 1.2), PromptInteractive('thighhighs', 1.0)], ['white'])
        >>> [x.name for x in p]
        ['%%%', 'thighhighs']
        """
        return [
            t.replace(self.replace_to) if t.name in self.excludes else t for t in prompt
        ]


class ExcludeCommand(Command):
    def __init__(
        self,
        excludes: Sequence[str],
    ):
        self.excludes = excludes

    def execute(self, prompt: Prompt) -> MutablePrompt:
        """
        >>> from lib.common import PromptInteractive
        >>> p = exclude([PromptInteractive('white hair', 1.2), PromptInteractive('thighhighs', 1.0)], ['white'])
        >>> [x.name for x in p]
        ['thighhighs']
        """
        return [t for t in prompt if t.name not in self.excludes]


class SortAllCommand(Command):
    def __init__(
        self,
        sorted_partial: functools.partial,
        reverse: bool = False,
    ):
        self.sorted_partial = sorted_partial
        self.reverse = reverse

    def execute(
        self,
        prompt: Prompt,
    ) -> MutablePrompt:
        return self.sorted_partial(prompt, reverse=self.reverse)


class RoundUpCommand(Command):
    def __init__(
        self,
        digits: int,
    ):
        self.digits = digits

    def execute(
        self,
        prompt: Prompt,
    ) -> MutablePrompt:
        def round_prompt(p: TokenInterface) -> TokenInterface:
            return type(p)(p.name, round(p.strength, self.digits))

        return list(map(round_prompt, prompt))


class RandomCommand(Command):
    def execute(
        self,
        prompt: Prompt,
    ) -> MutablePrompt:
        if isinstance(prompt, typing.MutableSequence):
            random.shuffle(prompt)
            return prompt
        else:
            return random.sample(prompt, len(prompt))


class SortCommand(Command):
    def __init__(
        self,
        reverse: bool = False,
    ):
        self.reverse = reverse

    def execute(
        self,
        prompt: Prompt,
    ) -> MutablePrompt:
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
        tokens = collect_same_tokens_sorted(prompt, self.reverse)
        return list(itertools.chain.from_iterable(tokens))


class UniqueCommand(Command):
    def __init__(
        self,
        reverse: bool = False,
    ):
        self.reverse = reverse

    def execute(
        self,
        prompt: Prompt,
    ) -> MutablePrompt:
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
