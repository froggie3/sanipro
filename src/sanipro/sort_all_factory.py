import functools
import logging

from . import utils
from .abc import TokenInterface

logger = logging.getLogger(__name__)

available = ("lexicographical", "length", "strength", "ord-sum", "ord-average")


def sort_lexicographically(token: TokenInterface) -> str:
    return token.name


def sort_by_ord_sum(token: TokenInterface) -> int:
    return sum(ord(char) for char in token.name)


def sort_by_length(token: TokenInterface) -> int:
    return token.length


def sort_by_strength(token: TokenInterface) -> float:
    return token.strength


def apply_from(keyword: str):
    funcs = (sort_lexicographically, sort_by_length, sort_by_strength, sort_by_ord_sum)

    try:
        matched = utils.ModuleMatcher(available, funcs).match(keyword)
        return functools.partial(sorted, key=matched)
    except NotImplementedError:
        raise NotImplementedError(f"no matched sort law for {keyword!r}")
