import argparse
import logging

from sanipro.abc import MutablePrompt, Prompt
from sanipro.commandline.help_formatter import SaniproHelpFormatter

from .abc import Command
from .filter import Filter

logger = logging.getLogger(__name__)


class ResetCommand(Command):
    new_value: float

    def __init__(self, new_value: float | None = None) -> None:
        super().__init__()
        if new_value is None:
            self.new_value = 1.0
        else:
            self.new_value = new_value

    def execute(self, prompt: Prompt) -> MutablePrompt:
        return [token.replace(new_weight=self.new_value) for token in prompt]

    @staticmethod
    def inject_subparser(subparser: argparse._SubParsersAction):
        subcommand = subparser.add_parser(
            Filter.RESET,
            formatter_class=SaniproHelpFormatter,
            help="Initializes all the weight of the tokens.",
            description="Initializes all the weight of the tokens.",
        )

        subcommand.add_argument(
            "-v",
            "--value",
            default=None,
            type=int,
            help="Fixed randomness to this value.",
        )
