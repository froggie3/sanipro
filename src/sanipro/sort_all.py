import functools
import logging

from . import utils
from .abc import TokenInterface
from .utils import KeyVal

logger = logging.getLogger(__name__)


def sort_lexicographically(token: TokenInterface) -> str:
    return token.name


def sort_by_ord_sum(token: TokenInterface) -> int:
    return sum(ord(char) for char in token.name)


def sort_by_length(token: TokenInterface) -> int:
    return token.length


def sort_by_strength(token: TokenInterface) -> float:
    return token.strength


class Available(utils.CommandModuleMap):
    LEXICOGRAPHICAL = KeyVal("lexicographical", sort_lexicographically)
    LENGTH = KeyVal("length", sort_by_length)
    STRENGTH = KeyVal("strength", sort_by_strength)
    ORD_SUM = KeyVal("ord-sum", sort_by_ord_sum)


def apply_from(*, method: str | None = None) -> functools.partial:
    """
    method を具体的なクラスの名前にマッチングさせる。

    Argument:
        method: コマンドラインで指定された方法.
    """
    # set default
    default = Available.LEXICOGRAPHICAL.key
    if method is None:
        method = default

    mapper = utils.ModuleMatcher(Available)
    try:
        partial = functools.partial(sorted, key=mapper.match(method))
        return partial
    except KeyError:
        raise ValueError("method name is not found.")
