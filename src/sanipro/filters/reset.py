import argparse
import logging

from sanipro.abc import MutablePrompt, Prompt
from sanipro.commandline.help_formatter import SaniproHelpFormatter

from .abc import Command

logger = logging.getLogger(__name__)


class ResetCommand(Command):
    command_id: str = "reset"
    new_value: float

    def __init__(self, new_value: float | None = None) -> None:
        super().__init__()
        if new_value is None:
            self.new_value = 1.0
        else:
            self.new_value = new_value

    def execute(self, prompt: Prompt) -> MutablePrompt:
        return [token.replace(new_weight=self.new_value) for token in prompt]

    @classmethod
    def inject_subparser(cls, subparser: argparse._SubParsersAction):
        subcommand = subparser.add_parser(
            cls.command_id,
            formatter_class=SaniproHelpFormatter,
            help="Initializes all the weight of the tokens.",
            description="Initializes all the weight of the tokens.",
        )

        subcommand.add_argument(
            "-v",
            "--value",
            default=1.0,
            type=float,
            help="Fixes the weight to this value.",
        )
