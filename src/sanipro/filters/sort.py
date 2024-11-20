import argparse
import logging
from itertools import chain

from sanipro.abc import MutablePrompt, Prompt
from sanipro.filters.utils import collect_same_tokens_sorted
from sanipro.help_formatter import SaniproHelpFormatter

from .abc import Command
from .filter import Filter

logger = logging.getLogger(__name__)


class SortCommand(Command):
    def __init__(self, reverse: bool = False):
        self.reverse = reverse

    def execute(self, prompt: Prompt) -> MutablePrompt:
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
        return list(chain(*collect_same_tokens_sorted(prompt, self.reverse)))

    @staticmethod
    def inject_subparser(subparser: argparse._SubParsersAction):
        subcommand = subparser.add_parser(
            Filter.SORT,
            formatter_class=SaniproHelpFormatter,
            help="Reorders duplicate tokens.",
            description="Reorders duplicate tokens.",
            epilog="This command reorders tokens with their weights by default.",
        )

        subcommand.add_argument(
            "-r", "--reverse", action="store_true", help="With reversed order."
        )
