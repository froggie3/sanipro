import logging

from sanipro.abc import MutablePrompt, Prompt
from sanipro.filters.abc import ExecutePrompt
from sanipro.filters.utils import collect_same_tokens_sorted

logger = logging.getLogger(__name__)


class UniqueCommand(ExecutePrompt):
    def __init__(self, reverse: bool = False):
        self.reverse = reverse

    def execute_prompt(self, prompt: Prompt) -> MutablePrompt:
        """
        >>> from lib.common import PromptInteractive
        >>> p = unique([PromptInteractive('white hair', 1.2), PromptInteractive('white hair', 1.0)])
        >>> [(x.name, x.weight) for x in p]
        [('white hair', 1.0)]

        >>> from lib.common import PromptInteractive
        >>> p = unique([PromptInteractive('white hair', 1.2), PromptInteractive('white hair', 1.0)], True)
        >>> [(x.name, x.weight) for x in p]
        [('white hair', 1.2)]
        """
        return [vals[0] for vals in collect_same_tokens_sorted(prompt, self.reverse)]
