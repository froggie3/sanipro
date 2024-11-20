import argparse
import logging
import random
import typing

from sanipro.abc import MutablePrompt, Prompt
from sanipro.help_formatter import SaniproHelpFormatter

from .abc import Command
from .filter import Filter

logger = logging.getLogger(__name__)


class RandomCommand(Command):
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

    @staticmethod
    def inject_subparser(subparser: argparse._SubParsersAction):
        subcommand = subparser.add_parser(
            Filter.RANDOM,
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
