from collections.abc import Sequence

from sanipro.abc import MutablePrompt, Prompt, TokenInterface
from sanipro.filters.abc import ExecutePrompt


class MaskCommand(ExecutePrompt):
    def __init__(self, excludes: Sequence[str], replace_to: str):
        self.excludes = excludes
        self.replace_to = replace_to

    def _replace_on_found(self, needle: TokenInterface):
        replaced = needle.name
        for item in self.excludes:
            replaced = replaced.replace(item, self.replace_to)

        return needle.replace(new_name=replaced)

    def execute_prompt(self, prompt: Prompt) -> MutablePrompt:
        return [self._replace_on_found(token) for token in prompt]
