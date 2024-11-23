import collections
import logging
import typing
from collections.abc import Mapping

from sanipro.filters import sort_all

from ..abc import MutablePrompt, Prompt, TokenInterface

logger = logging.getLogger(__name__)


def collect_same_tokens(prompts: Prompt) -> Mapping[str, MutablePrompt]:
    groups = collections.defaultdict(list)
    for prompt in prompts:
        groups[prompt.name].append(prompt)
    return groups


def collect_same_tokens_sorted(
    prompt: Prompt, reverse=False
) -> typing.Generator[list[TokenInterface], None, None]:
    f = sort_all.sort_by_weight
    return (
        sorted(token, key=f, reverse=reverse)
        for token in collect_same_tokens(prompt).values()
    )


if __name__ == "__main__":
    import doctest

    doctest.testmod()
