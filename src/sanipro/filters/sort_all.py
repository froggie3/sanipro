import argparse
import functools
import logging
from functools import partial

from sanipro.abc import MutablePrompt, Prompt, TokenInterface
from sanipro.commandline.help_formatter import SaniproHelpFormatter
from sanipro.utils import CommandModuleMap, KeyVal, ModuleMatcher

from .abc import Command
from .filter import Filter

logger = logging.getLogger(__name__)


def sort_lexicographically(token: TokenInterface) -> str:
    return token.name


def sort_by_ord_sum(token: TokenInterface) -> int:
    return sum(ord(char) for char in token.name)


def sort_by_length(token: TokenInterface) -> int:
    return token.length


def sort_by_strength(token: TokenInterface) -> float:
    return token.strength


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

    mapper = ModuleMatcher(Available)
    try:
        partial = functools.partial(sorted, key=mapper.match(method))
        return partial
    except KeyError:
        raise ValueError("method name is not found.")


class Available(CommandModuleMap):
    LEXICOGRAPHICAL = KeyVal("lexicographical", sort_lexicographically)
    LENGTH = KeyVal("length", sort_by_length)
    STRENGTH = KeyVal("strength", sort_by_strength)
    ORD_SUM = KeyVal("ord-sum", sort_by_ord_sum)


class SortAllCommand(Command):
    def __init__(self, sorted_partial: partial, reverse: bool = False):
        self.sorted_partial = sorted_partial
        self.reverse = reverse

    def execute(self, prompt: Prompt) -> MutablePrompt:
        return self.sorted_partial(prompt, reverse=self.reverse)

    @staticmethod
    def inject_subparser(subparser: argparse._SubParsersAction):
        sort_all_subparser = subparser.add_parser(
            Filter.SORT_ALL,
            formatter_class=SaniproHelpFormatter,
            help="Reorders all the prompts.",
            description="Reorders all the prompts.",
        )

        sort_all_subparser.add_argument(
            "-r", "--reverse", action="store_true", help="With reversed order."
        )

        subcommand = sort_all_subparser.add_subparsers(
            title=Filter.SORT_ALL,
            description="The available method to sort the tokens.",
            dest="sort_all_method",
            metavar="METHOD",
        )

        subcommand.add_parser(
            Available.LEXICOGRAPHICAL.key,
            help="Sort the prompt with lexicographical order. Familiar sort method.",
        )

        subcommand.add_parser(
            Available.LENGTH.key,
            help=(
                "Reorder the token length."
                "This behaves slightly similar as 'ord-sum' method."
            ),
        )

        subcommand.add_parser(
            Available.STRENGTH.key, help="Reorder the tokens by their weights."
        )

        subcommand.add_parser(
            Available.ORD_SUM.key,
            help=(
                "Reorder the tokens by its sum of character codes."
                "This behaves slightly similar as 'length' method."
            ),
        )
