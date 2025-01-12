from sanipro.abc import MutablePrompt, Prompt, TokenInterface
from sanipro.filters.abc import ExecutePrompt


class TranslateTokenTypeCommand(ExecutePrompt):
    def __init__(self, target_type: type[TokenInterface]):
        self.target_type = target_type

    def execute_prompt(self, prompt: Prompt) -> MutablePrompt:
        return [self.target_type(token.name, token.weight) for token in prompt]
