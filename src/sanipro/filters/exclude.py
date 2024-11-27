import logging
from collections.abc import Sequence

from sanipro.abc import MutablePrompt, Prompt

from .abc import Command

logger = logging.getLogger(__name__)


class ExcludeCommand(Command):
    command_id: str = "exclude"

    def __init__(self, excludes: Sequence[str]):
        self.excludes = excludes

    def execute(self, prompt: Prompt) -> MutablePrompt:
        """
        >>> from lib.common import PromptInteractive
        >>> p = exclude([PromptInteractive('white hair', 1.2), PromptInteractive('thighhighs', 1.0)], ['white'])
        >>> [x.name for x in p]
        ['thighhighs']
        """
        return [token for token in prompt if token.name not in self.excludes]
