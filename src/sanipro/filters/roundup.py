from sanipro import utils
from sanipro.abc import MutablePrompt, Prompt
from sanipro.filters.abc import ExecutePrompt


class RoundUpCommand(ExecutePrompt):
    def __init__(self, digits: int):
        self.digits = digits

    def execute_prompt(self, prompt: Prompt) -> MutablePrompt:
        return [utils.round_token_weight(token, self.digits) for token in prompt]
