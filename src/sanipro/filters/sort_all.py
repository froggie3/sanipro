import logging
from functools import partial

from sanipro.abc import MutablePrompt, Prompt

from .abc import Command

logger = logging.getLogger(__name__)


class SortAllCommand(Command):
    command_id: str = "sort-all"

    def __init__(self, sorted_partial: partial, reverse: bool = False):
        self.sorted_partial = sorted_partial
        self.reverse = reverse

    def execute(self, prompt: Prompt) -> MutablePrompt:
        return self.sorted_partial(prompt, reverse=self.reverse)
