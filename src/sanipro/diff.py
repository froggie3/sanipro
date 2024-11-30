from collections.abc import Set

from sanipro.common import MutablePrompt
from sanipro.filters.utils import collect_same_tokens


class PromptDifferenceDetector:
    """Detects the difference between the two prompts."""

    before_num: int
    after_num: int
    reduced_num: int
    duplicated: Set[str]

    def __init__(self, before_process: MutablePrompt, after_process: MutablePrompt):
        self.before_num = len(before_process)
        self.after_num = len(after_process)
        self.reduced_num = self.before_num - self.after_num

        THRESHOULD = 1
        self.duplicated = set()
        for key, tokens in collect_same_tokens(before_process).items():
            if len(tokens) > THRESHOULD:
                self.duplicated.add(key)
