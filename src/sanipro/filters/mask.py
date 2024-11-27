import argparse
import logging
from collections.abc import Sequence

from sanipro.abc import MutablePrompt, Prompt
from sanipro.commandline.help_formatter import SaniproHelpFormatter

from .abc import Command

logger = logging.getLogger(__name__)


class MaskCommand(Command):
    command_id: str = "mask"

    def __init__(self, excludes: Sequence[str], replace_to: str):
        self.excludes = excludes
        self.replace_to = replace_to

    def execute(self, prompt: Prompt) -> MutablePrompt:
        """
        >>> from lib.common import PromptInteractive
        >>> p = mask([PromptInteractive('white hair', 1.2), PromptInteractive('thighhighs', 1.0)], ['white'])
        >>> [x.name for x in p]
        ['%%%', 'thighhighs']
        """
        return [
            (
                token.replace(new_name=self.replace_to)
                if token.name in self.excludes
                else token
            )
            for token in prompt
        ]

    @classmethod
    def inject_subparser(cls, subparser: argparse._SubParsersAction):
        subcommand = subparser.add_parser(
            cls.command_id,
            help="Mask tokens with words.",
            description="Mask words specified with another word (optional).",
            formatter_class=SaniproHelpFormatter,
            epilog=(
                (
                    "Note that you can still use the global `--exclude` option"
                    "as well as this filter."
                )
            ),
        )

        subcommand.add_argument("mask", nargs="*", type=str, help="Masks this word.")

        subcommand.add_argument(
            "-t",
            "--replace-to",
            type=str,
            default=r"%%%",
            help="The new character or string replaced to.",
        )
