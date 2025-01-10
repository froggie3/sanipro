from collections.abc import Callable

from sanipro.abc import MutablePrompt, Prompt
from sanipro.filters.abc import ExecutePrompt


class SortAllCommand(ExecutePrompt):
    def __init__(self, key: Callable, reverse: bool = False):
        self.key = key
        self.reverse = reverse

    def execute_prompt(self, prompt: Prompt) -> MutablePrompt:
        return sorted(prompt, key=self.key, reverse=self.reverse)
