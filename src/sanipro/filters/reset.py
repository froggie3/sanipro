from sanipro.abc import MutablePrompt, Prompt
from sanipro.filters.abc import ExecutePrompt


class ResetCommand(ExecutePrompt):
    new_value: float

    def __init__(self, new_value: float | None = None) -> None:
        super().__init__()
        if new_value is None:
            self.new_value = 1.0
        else:
            self.new_value = new_value

    def execute_prompt(self, prompt: Prompt) -> MutablePrompt:
        return [token.replace(new_weight=self.new_value) for token in prompt]
