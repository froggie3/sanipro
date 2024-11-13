import functools
import logging
import typing
from collections.abc import Sequence

from . import sort_all_factory
from .abc import MutablePrompt, Prompt, TokenInterface

logger = logging.getLogger(__name__)


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


def mask(
    prompts: Prompt,
    excludes: Sequence[str],
    replace_to: str,
) -> MutablePrompt:
    """
    >>> from lib.common import PromptInteractive
    >>> p = mask([PromptInteractive('white hair', 1.2), PromptInteractive('thighhighs', 1.0)], ['white'])
    >>> [x.name for x in p]
    ['%%%', 'thighhighs']
    """
    filtered_prompts = []
    for prompt in prompts:
        for excluded in excludes:
            if excluded in prompt.name:
                filtered_prompts.append(prompt.replace(replace_to))
                break
        else:
            filtered_prompts.append(prompt)
    return filtered_prompts


class Mask(typing.Protocol):
    def __call__(
        self, prompts: Prompt, excludes: Sequence[str], replace_to: str
    ) -> MutablePrompt: ...


def exclude(
    prompts: Prompt,
    excludes: Sequence[str],
) -> MutablePrompt:
    """
    >>> from lib.common import PromptInteractive
    >>> p = exclude([PromptInteractive('white hair', 1.2), PromptInteractive('thighhighs', 1.0)], ['white'])
    >>> [x.name for x in p]
    ['thighhighs']
    """
    filtered_prompts = []
    for prompt in prompts:
        for excluded in excludes:
            if excluded not in prompt.name:
                filtered_prompts.append(prompt)
                break
        else:
            continue
    return filtered_prompts


class Exclude(typing.Protocol):
    def __call__(self, prompts: Prompt, excludes: Sequence[str]) -> MutablePrompt: ...


def sort_all(
    prompts: Prompt,
    sorted_partial: functools.partial,
    *,
    reverse=False,
) -> MutablePrompt:
    """
    sort all the prompts by an algolithm.
    """
    return sorted_partial(prompts, reverse=reverse)


class SortAll(typing.Protocol):
    def __call__(
        self, prompts: Prompt, sorted_partial: functools.partial, *, reverse=False
    ) -> MutablePrompt: ...


def round_up(
    prompts: Prompt,
    digits: int,
) -> Prompt:

    def f(dgt: int) -> typing.Callable:
        def g(p: TokenInterface) -> TokenInterface:
            cls = type(p)
            return cls(p.name, round(p.strength, dgt))

        return g

    prompts = list(map(f(digits), prompts))
    return prompts


class RoundUp(typing.Protocol):
    def __call__(self, prompts: Prompt, digits: int) -> Prompt: ...


def random(
    prompts: Prompt,
) -> Prompt:
    import random

    if isinstance(prompts, typing.MutableSequence):
        random.shuffle(prompts)
        return prompts
    else:
        return random.sample(prompts, len(prompts))


class Random(typing.Protocol):
    def __call__(self, prompts: Prompt) -> Prompt: ...


def sort(
    prompts: Prompt,
    *,
    reverse=False,
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
        v = sorted(v, key=sort_all_factory.sort_by_strength, reverse=reverse)
        for item in v:
            tokens.append(item)

    return tokens


class Sort(typing.Protocol):
    def __call__(self, prompts: Prompt, *, reverse=False) -> MutablePrompt: ...


def unique(
    prompts: Prompt,
    *,
    reverse=False,
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
        v = sorted(v, key=sort_all_factory.sort_by_strength, reverse=reverse)
        tokens.append(v.pop(0))

    return tokens


class Unique(typing.Protocol):
    def __call__(self, prompts: Prompt, *, reverse=False) -> MutablePrompt: ...


Filters = Mask | Exclude | SortAll | RoundUp | Random | Sort | Unique


if __name__ == "__main__":
    import doctest

    doctest.testmod()
