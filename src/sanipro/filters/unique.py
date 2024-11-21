import argparse
import logging

from sanipro.abc import MutablePrompt, Prompt
from sanipro.commandline.help_formatter import SaniproHelpFormatter
from sanipro.filters.utils import collect_same_tokens_sorted

from .abc import Command
from .filter import Filter

logger = logging.getLogger(__name__)


class UniqueCommand(Command):
    def __init__(self, reverse: bool = False):
        self.reverse = reverse

    def execute(self, prompt: Prompt) -> MutablePrompt:
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
        return [vals[0] for vals in collect_same_tokens_sorted(prompt, self.reverse)]

    @staticmethod
    def inject_subparser(subparser: argparse._SubParsersAction):
        subparser_unique = subparser.add_parser(
            Filter.UNIQUE,
            formatter_class=SaniproHelpFormatter,
            help="Removes duplicated tokens, and uniquify them.",
            description="Removes duplicated tokens, and uniquify them.",
            epilog="",
        )

        subparser_unique.add_argument(
            "-r",
            "--reverse",
            action="store_true",
            help="Make the token with the heaviest weight survived.",
        )
