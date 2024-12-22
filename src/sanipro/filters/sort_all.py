import logging
from functools import partial

from sanipro.abc import MutablePrompt, Prompt
from sanipro.filters.abc import ExecutePrompt

logger = logging.getLogger(__name__)


class SortAllCommand(ExecutePrompt):
    def __init__(self, sorted_partial: partial, reverse: bool = False):
        self.sorted_partial = sorted_partial
        self.reverse = reverse

    def execute_prompt(self, prompt: Prompt) -> MutablePrompt:
        return self.sorted_partial(prompt, reverse=self.reverse)
