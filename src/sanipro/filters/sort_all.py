import logging
from functools import partial

from sanipro.abc import MutablePrompt, Prompt
from sanipro.filters.abc import Command

logger = logging.getLogger(__name__)


class SortAllCommand(Command):
    def __init__(self, sorted_partial: partial, reverse: bool = False):
        self.sorted_partial = sorted_partial
        self.reverse = reverse

    def execute(self, prompt: Prompt) -> MutablePrompt:
        return self.sorted_partial(prompt, reverse=self.reverse)
