import logging

from sanipro.abc import MutablePrompt, Prompt
from sanipro.filters.abc import Command
from sanipro.filters.utils import collect_same_tokens_sorted

logger = logging.getLogger(__name__)


class UniqueCommand(Command):
    command_id: str = "unique"

    def __init__(self, reverse: bool = False):
        self.reverse = reverse

    def execute(self, prompt: Prompt) -> MutablePrompt:
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
