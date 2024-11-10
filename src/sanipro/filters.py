import functools
import logging
import typing
from collections.abc import Sequence

from . import sort_all_factory, utils
from .abc import TokenInterface

logger = logging.getLogger(__name__)


def mask(
    prompts: Sequence[TokenInterface],
    excludes: Sequence[str],
    replace_to: str,
) -> list[TokenInterface]:
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


def exclude(
    prompts: Sequence[TokenInterface],
    excludes: Sequence[str],
) -> list[TokenInterface]:
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


def collect_same_prompt(
    prompts: Sequence[TokenInterface],
):
    groups: dict[str, list[TokenInterface]] = {}
    for prompt in prompts:
        if prompt.name in groups:
            groups[prompt.name].append(prompt)
        else:
            groups[prompt.name] = [prompt]
    return groups


def sort_all(
    prompts: Sequence[TokenInterface],
    sorted_partial: functools.partial,
    *,
    reverse=False,
) -> list[TokenInterface]:
    """
    sort all the prompts by an algolithm.
    """
    return sorted_partial(prompts, reverse=reverse)

def round_up(
    prompts: Sequence[TokenInterface],
    digits: int,
) -> Sequence[TokenInterface]:
    
    def f(dgt: int) -> typing.Callable:
        def g(p: TokenInterface) -> TokenInterface:
            cls = type(p)
            return cls(p.name, round(p.strength, dgt))
        return g

    prompts = list(map(f(digits), prompts))
    return prompts

def random(
    prompts: Sequence[TokenInterface],
) -> Sequence[TokenInterface]:
    import random

    if isinstance(prompts, typing.MutableSequence):
        random.shuffle(prompts)
        return prompts
    else:
        return random.sample(prompts, len(prompts))


def sort(
    prompts: Sequence[TokenInterface],
    *,
    reverse=False,
) -> list[TokenInterface]:
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
    groups = collect_same_prompt(prompts)

    prompts = []
    for k, v in groups.items():
        v = utils.sorted(v, key=sort_all_factory.sort_by_strength, reverse=reverse)
        for item in v:
            prompts.append(item)

    return prompts


def unique(
    prompts: Sequence[TokenInterface],
    *,
    reverse=False,
) -> list[TokenInterface]:
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
    groups = collect_same_prompt(prompts)

    prompts = []
    for k, v in groups.items():
        v = utils.sorted(v, key=sort_all_factory.sort_by_strength, reverse=reverse)
        if len(v) > 1:
            logger.debug(f"duplicates found: {v!r}")
        prompts.append(v.pop(0))

    return prompts


if __name__ == "__main__":
    import doctest

    doctest.testmod()
