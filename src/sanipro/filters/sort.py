import logging
from itertools import chain

from sanipro.abc import MutablePrompt, Prompt
from sanipro.filters.abc import Command
from sanipro.filters.utils import collect_same_tokens_sorted

logger = logging.getLogger(__name__)


class SortCommand(Command):
    command_id: str = "sort"

    def __init__(self, reverse: bool = False):
        self.reverse = reverse

    def execute(self, prompt: Prompt) -> MutablePrompt:
        """
        >>> from lib.common import PromptInteractive
        >>> p = sort([PromptInteractive('white hair', 1.2), PromptInteractive('white hair', 1.0)])
        >>> [(x.name, x.weight) for x in p]
        [('white hair', 1.0), ('white hair', 1.2)]

        >>> from lib.common import PromptInteractive
        >>> p = sort([PromptInteractive('white hair', 1.2), PromptInteractive('white hair', 1.0)], True)
        >>> [(x.name, x.weight) for x in p]
        [('white hair', 1.2), ('white hair', 1.0)]
        """
        return list(chain(*collect_same_tokens_sorted(prompt, self.reverse)))
