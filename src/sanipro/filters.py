import functools
import logging
import random
import typing
from abc import ABC, abstractmethod
from collections.abc import Sequence

from . import sort_all_factory
from .abc import MutablePrompt, Prompt, TokenInterface

logger = logging.getLogger(__name__)


class Command(ABC):
    @abstractmethod
    def execute(
        self,
        prompts: Prompt,
    ) -> MutablePrompt:
        raise NotImplementedError


def collect_same_prompt(
    prompts: Prompt,
) -> dict[str, MutablePrompt]:
    groups = {}
    for prompt in prompts:
        if prompt.name in groups:
            groups[prompt.name].append(prompt)
        else:
            groups[prompt.name] = [prompt]
    return groups


def collect_same_prompt_generator(
    prompts: Prompt,
) -> typing.Generator[tuple[str, MutablePrompt], None, None]:
    groups = collect_same_prompt(prompts)
    for k, v in groups.items():
        yield k, v


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
        prompts: Prompt,
    ) -> MutablePrompt:
        """
        >>> from lib.common import PromptInteractive
        >>> p = mask([PromptInteractive('white hair', 1.2), PromptInteractive('thighhighs', 1.0)], ['white'])
        >>> [x.name for x in p]
        ['%%%', 'thighhighs']
        """
        filtered_prompts = []
        for prompt in prompts:
            for excluded in self.excludes:
                if excluded in prompt.name:
                    filtered_prompts.append(prompt.replace(self.replace_to))
                    break
            else:
                filtered_prompts.append(prompt)
        return filtered_prompts


class ExcludeCommand(Command):
    def __init__(
        self,
        excludes: Sequence[str],
    ):
        self.excludes = excludes

    def execute(self, prompts: Prompt) -> MutablePrompt:
        """
        >>> from lib.common import PromptInteractive
        >>> p = exclude([PromptInteractive('white hair', 1.2), PromptInteractive('thighhighs', 1.0)], ['white'])
        >>> [x.name for x in p]
        ['thighhighs']
        """
        filtered_prompts = []
        for prompt in prompts:
            for excluded in self.excludes:
                if excluded not in prompt.name:
                    filtered_prompts.append(prompt)
                    break
        return filtered_prompts


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
        prompts: Prompt,
    ) -> MutablePrompt:
        return self.sorted_partial(prompts, reverse=self.reverse)


class RoundUpCommand(Command):
    def __init__(
        self,
        digits: int,
    ):
        self.digits = digits

    def execute(
        self,
        prompts: Prompt,
    ) -> MutablePrompt:
        def round_prompt(p: TokenInterface) -> TokenInterface:
            return type(p)(p.name, round(p.strength, self.digits))

        return list(map(round_prompt, prompts))


class RandomCommand(Command):
    def execute(
        self,
        prompts: Prompt,
    ) -> MutablePrompt:
        if isinstance(prompts, typing.MutableSequence):
            random.shuffle(prompts)
            return prompts
        else:
            return random.sample(prompts, len(prompts))


class SortCommand(Command):
    def __init__(
        self,
        reverse: bool = False,
    ):
        self.reverse = reverse

    def execute(
        self,
        prompts: Prompt,
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
        tokens = []
        for _, v in collect_same_prompt_generator(prompts):
            v = sorted(v, key=sort_all_factory.sort_by_strength, reverse=self.reverse)
            for item in v:
                tokens.append(item)

        return tokens


class UniqueCommand(Command):
    def __init__(
        self,
        reverse: bool = False,
    ):
        self.reverse = reverse

    def execute(
        self,
        prompts: Prompt,
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
        tokens = []
        for _, v in collect_same_prompt_generator(prompts):
            v = sorted(v, key=sort_all_factory.sort_by_strength, reverse=self.reverse)
            tokens.append(v.pop(0))

        return tokens


if __name__ == "__main__":
    import doctest

    doctest.testmod()
