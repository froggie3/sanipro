from collections.abc import Sequence

from sanipro.abc import MutablePrompt, Prompt, TokenInterface
from sanipro.filters.abc import ExecutePrompt


class ExcludeCommand(ExecutePrompt):
    def __init__(self, excludes: Sequence[str]):
        self.excludes = excludes

    def _found_in_excluded(self, needle: TokenInterface):
        for item in self.excludes:
            if item in needle.name:
                return True
        return False

    def execute_prompt(self, prompt: Prompt) -> MutablePrompt:
        return [token for token in prompt if not self._found_in_excluded(token)]
