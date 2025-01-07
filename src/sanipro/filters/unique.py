from sanipro.abc import MutablePrompt, Prompt
from sanipro.filters.abc import ExecutePrompt
from sanipro.filters.utils import collect_same_tokens_sorted


class UniqueCommand(ExecutePrompt):
    def __init__(self, reverse: bool = False):
        self.reverse = reverse

    def execute_prompt(self, prompt: Prompt) -> MutablePrompt:
        return [vals[0] for vals in collect_same_tokens_sorted(prompt, self.reverse)]
