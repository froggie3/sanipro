import logging
from functools import partial

from sanipro.abc import MutablePrompt, Prompt
from sanipro.compatible import Self
from sanipro.filters.utils import (
    sort_by_length,
    sort_by_ord_sum,
    sort_by_weight,
    sort_lexicographically,
)
from sanipro.utils import CommandModuleMap, KeyVal, ModuleMatcher

from .abc import Command

logger = logging.getLogger(__name__)


class Available(CommandModuleMap):
    LEXICOGRAPHICAL = KeyVal("lexicographical", sort_lexicographically)
    LENGTH = KeyVal("length", sort_by_length)
    STRENGTH = KeyVal("weight", sort_by_weight)
    ORD_SUM = KeyVal("ord-sum", sort_by_ord_sum)


class SortAllCommand(Command):
    command_id: str = "sort-all"

    def __init__(self, sorted_partial: partial, reverse: bool = False):
        self.sorted_partial = sorted_partial
        self.reverse = reverse

    def execute(self, prompt: Prompt) -> MutablePrompt:
        return self.sorted_partial(prompt, reverse=self.reverse)
