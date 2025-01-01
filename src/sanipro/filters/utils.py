import collections
import typing
from collections.abc import Mapping

from sanipro.abc import MutablePrompt, Prompt, TokenInterface


def collect_same_tokens(prompts: Prompt) -> Mapping[str, MutablePrompt]:
    groups = collections.defaultdict(list)
    for prompt in prompts:
        groups[prompt.name].append(prompt)
    return groups


def sort_lexicographically(token: TokenInterface) -> str:
    return token.name


def sort_by_ord_sum(token: TokenInterface) -> int:
    return sum(ord(char) for char in token.name)


def sort_by_length(token: TokenInterface) -> int:
    return token.length


def sort_by_weight(token: TokenInterface) -> float:
    return token.weight


def collect_same_tokens_sorted(
    prompt: Prompt, reverse=False
) -> typing.Generator[list[TokenInterface], None, None]:
    f = sort_by_weight
    return (
        sorted(token, key=f, reverse=reverse)
        for token in collect_same_tokens(prompt).values()
    )


if __name__ == "__main__":
    import doctest

    doctest.testmod()
