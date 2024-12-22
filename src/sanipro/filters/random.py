import logging
import random
import typing

from sanipro.abc import MutablePrompt, Prompt
from sanipro.filters.abc import ExecutePrompt

logger = logging.getLogger(__name__)


class RandomCommand(ExecutePrompt):
    def __init__(self, seed: int | None = None):
        self.seed = seed

    def execute_prompt(self, prompt: Prompt) -> MutablePrompt:
        if self.seed is not None:
            random.seed(self.seed)

        if not isinstance(prompt, typing.MutableSequence):
            _prompt = random.sample(prompt, len(prompt))
            return _prompt

        random.shuffle(prompt)
        return prompt
