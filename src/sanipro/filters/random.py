import argparse
import logging
import random
import typing

from sanipro.abc import MutablePrompt, Prompt
from sanipro.commandline.help_formatter import SaniproHelpFormatter

from .abc import Command

logger = logging.getLogger(__name__)


class RandomCommand(Command):
    command_id: str = "random"

    def __init__(self, seed: int | None = None):
        self.seed = seed

    def execute(self, prompt: Prompt) -> MutablePrompt:
        if self.seed is not None:
            random.seed(self.seed)

        if not isinstance(prompt, typing.MutableSequence):
            _prompt = random.sample(prompt, len(prompt))
            return _prompt

        random.shuffle(prompt)
        return prompt

    @classmethod
    def inject_subparser(cls, subparser: argparse._SubParsersAction):
        subcommand = subparser.add_parser(
            cls.command_id,
            formatter_class=SaniproHelpFormatter,
            help="Shuffles all the prompts altogether.",
            description="Shuffles all the prompts altogether.",
        )

        subcommand.add_argument(
            "-b",
            "--seed",
            default=None,
            type=int,
            help="Fixed randomness to this value.",
        )
