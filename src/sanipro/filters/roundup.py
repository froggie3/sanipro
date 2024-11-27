import argparse
import logging

from sanipro import utils
from sanipro.abc import MutablePrompt, Prompt

from .abc import Command

logger = logging.getLogger(__name__)


class RoundUpCommand(Command):
    command_id: str = "mask"

    def __init__(self, digits: int):
        self.digits = digits

    def execute(self, prompt: Prompt) -> MutablePrompt:
        return [utils.round_token_weight(token, self.digits) for token in prompt]

    @classmethod
    def inject_subparser(cls, subparser: argparse._SubParsersAction): ...
