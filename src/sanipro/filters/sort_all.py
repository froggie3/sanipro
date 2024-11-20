import argparse
import logging
from functools import partial

from sanipro import sort_all
from sanipro.abc import MutablePrompt, Prompt
from sanipro.help_formatter import SaniproHelpFormatter

from .abc import Command
from .filter import Filter

logger = logging.getLogger(__name__)


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
            sort_all.Available.LEXICOGRAPHICAL.key,
            help="Sort the prompt with lexicographical order. Familiar sort method.",
        )

        subcommand.add_parser(
            sort_all.Available.LENGTH.key,
            help=(
                "Reorder the token length."
                "This behaves slightly similar as 'ord-sum' method."
            ),
        )

        subcommand.add_parser(
            sort_all.Available.STRENGTH.key, help="Reorder the tokens by their weights."
        )

        subcommand.add_parser(
            sort_all.Available.ORD_SUM.key,
            help=(
                "Reorder the tokens by its sum of character codes."
                "This behaves slightly similar as 'length' method."
            ),
        )
